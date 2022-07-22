import concurrent.futures

import nextcord
from nextcord.ext import commands
from yt_dlp import YoutubeDL
from beatrice.sound_manager import AudioFile, SoundManager


def _run_youtubedl(link):
    yt = YoutubeDL({"quiet": True, "no_warnings": True})
    selector = yt.build_format_selector("ba/b")
    info = yt.extract_info(link, process=False, download=False)
    # Probably won't evaluate if this happens???
    if "formats" not in info:
        return None, None
    video = yt.process_ie_result(info, download=False)
    try:
        format = list(selector(video))
        return format, info
    except KeyError:
        print("Error obtaining video")
        return None, None


class AudioQueue(dict):
    def __getitem__(self, item):
        if item not in self:
            super(AudioQueue, self).__setitem__(item, [])
        return super(AudioQueue, self).__getitem__(item)


class Youtube(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ppe = concurrent.futures.ProcessPoolExecutor()
        self.text_channels = {}
        self.sound_manager = None
        self.queue = AudioQueue()

    async def __async_init__(self):
        self.sound_manager: SoundManager = self.bot.cogs.get("SoundManager")

    def remember_channel(self, text_channel: nextcord.TextChannel):
        self.text_channels[text_channel.guild] = text_channel

    @commands.group("youtube", aliases=["yt", "music", "m"])
    async def yt_com_group(self, *args):
        if self.sound_manager is None:
            args[0].invoked_subcommand = None
            return True
        if args[0].invoked_subcommand is not None:
            return None
        if args[0].subcommand_passed is None:
            await self.queue_command(args[0])
        else:
            if args[0].subcommand_passed.startswith("http"):
                await self.queue_command(args[0], args[0].subcommand_passed)

    async def link_to_audio_file(self, link: str, guild: nextcord.Guild = None):
        if guild:
            guild = guild.id
        format, info = await self.bot.loop.run_in_executor(self.ppe, _run_youtubedl, link)
        if format is None and info is None:
            return None
        if "uploader" in info:
            title = f"{info['title']} - {info['uploader']}"
        else:
            title = f"{info['title']} - {info['webpage_url_domain']}"
        return AudioFile(format[0]["url"], volume=1, guild=guild, title=title, url=info["webpage_url"])

    async def output_queue(self, text_channel: nextcord.TextChannel):
        if len(self.queue[text_channel.guild]) == 0:
            await text_channel.send("Nothing is currently queued.")
            return
        status = await self.sound_manager.is_paused(text_channel.guild, "music")
        string = f"1) {self.queue[text_channel.guild][0].as_markdown()}{'' if status else ' 🎶'}"
        for i, audio_file in enumerate(self.queue[text_channel.guild][1:]):
            string += f"\n{i + 2}) {audio_file.as_markdown()}"
        await text_channel.send(embeds=[nextcord.Embed(
            description=string
        )])

    @yt_com_group.command("queue", aliases=["q"])
    async def queue_command(self, ctx: commands.Context, *args):
        self.text_channels[ctx.guild] = ctx.channel
        if len(args) == 0:
            await self.output_queue(ctx.channel)
            return
        if ctx.author.voice is None:
            await ctx.send("You aren't currently in a voice channel.")
            return
        async with ctx.channel.typing():
            audio_file = await self.link_to_audio_file(args[0], ctx.guild)
        if audio_file is None:
            await ctx.message.add_reaction("❔")
            return
        if len(self.queue[ctx.guild]) > 0:
            await ctx.send(embeds=[nextcord.Embed(
                description=f"Queued: {audio_file.as_markdown()}"
            )])
        self.queue[ctx.guild].append(audio_file)
        await self.sound_manager.queue(ctx.author, "music", audio_file, play_start=self.on_song_start, play_end=self.on_song_end)

    async def on_song_start(self, audio_file: AudioFile):
        guild = self.bot.get_guild(audio_file.guild)
        guild_queue = self.queue[guild]
        while guild_queue[0] != audio_file:
            guild_queue.pop(0)
        await self.text_channels[guild].send(embeds=[nextcord.Embed(
            description=f"Now playing: {audio_file.as_markdown()}"
        )])

    async def on_song_end(self, audio_file: AudioFile):
        guild = self.bot.get_guild(audio_file.guild)
        guild_queue = self.queue[guild]
        if len(guild_queue) > 0:
            if guild_queue[0] == audio_file:
                guild_queue.pop(0)
        print("File finished, removing from queue")

    @yt_com_group.command("stop")
    async def stop_command(self, ctx: commands.Context, *args):
        await self.sound_manager.stop(ctx.author.guild, "music")
        self.queue.clear()
        await ctx.send(embeds=[nextcord.Embed(
            description="Stopped music playback."
        )])

    @yt_com_group.command("pause")
    async def pause_command(self, ctx: commands.Context, *args):
        self.text_channels[ctx.guild] = ctx.channel
        status = await self.sound_manager.is_paused(ctx.guild, "music")
        if status is None:
            await ctx.send("Nothing is currently queued.")
            return
        if not status:
            await self.sound_manager.pause(ctx.author.guild, "music")
            await ctx.send("Playback paused.")
        else:
            await ctx.send("Playback already paused.")

    @yt_com_group.command("play")
    async def play_command(self, ctx: commands.Context, *args):
        self.text_channels[ctx.guild] = ctx.channel
        status = await self.sound_manager.is_paused(ctx.guild, "music")
        if status is None:
            await ctx.send("Nothing is currently queued.")
            return
        if await self.sound_manager.is_paused(ctx.guild, "music"):
            await self.sound_manager.play(ctx.author.guild, "music")
            await ctx.send("Playing...")
        else:
            await ctx.send("Already playing.")

    @yt_com_group.command("next")
    async def next_command(self, ctx: commands.Context, *args):
        queue = self.queue[ctx.guild]
        if len(queue) > 0:
            await self.sound_manager.next(ctx.guild, "music")

    @yt_com_group.command("remove")
    async def remove_command(self, ctx: commands.Context, *args):
        if len(args) == 0:
            await ctx.send("Nothing to remove.")
            return
        audio_file = await self.link_to_audio_file(args[0], ctx.guild)
        queue = self.queue[ctx.guild]
        if audio_file in queue:
            await ctx.send(embeds=[nextcord.Embed(
                description=f"Removing: {audio_file.as_markdown()}"
            )])
            await self.sound_manager.remove(ctx.guild, "music", audio_file)
            queue.remove(audio_file)
        else:
            await ctx.send("Song not found in queue.")

    @yt_com_group.command("help")
    async def help_command(self, ctx: commands.Context, *args):
        await ctx.send("```"
                       "Music can play music from YouTube and other YouTubeDL-compatible sites.\n"
                       "Usage:\n"
                       "    m <link>, m queue <link>, m q <link> - Queues a link and starts playing\n"
                       "    m, m queue, m q - View the current queue\n"
                       "    m pause - Pauses music\n"
                       "    m play - Unpauses music\n"
                       "    m stop - Stops playback and clears the queue\n"
                       "    m next - Skips to the next song in the queue\n"
                       "    m remove <link> - Removes the linked song from the queue\n"
                       "```")

    @commands.Cog.listener("on_close")
    async def close(self):
        self.ppe.shutdown(True)


def setup(bot):
    bot.add_cog(Youtube(bot))
