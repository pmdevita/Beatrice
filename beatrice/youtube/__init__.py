import nextcord
from nextcord.ext import commands
from yt_dlp import YoutubeDL
from beatrice.sound_manager import AudioFile, SoundManager


class AudioQueue(dict):
    def __getitem__(self, item):
        if item not in self:
            super(AudioQueue, self).__setitem__(item, [])
        return super(AudioQueue, self).__getitem__(item)


class Youtube(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.yt = YoutubeDL({"quiet": True, "no_warnings": True})
        self.selector = self.yt.build_format_selector("ba/b")
        self.text_channels = {}
        self.sound_manager = None
        self.queue = AudioQueue()

    async def __async_init__(self):
        self.sound_manager: SoundManager = self.bot.cogs.get("SoundManager")

    def remember_channel(self, text_channel: nextcord.TextChannel):
        self.text_channels[text_channel.guild] = text_channel

    @commands.group("youtube", aliases=["yt", "music"])
    async def yt_com_group(self, *args):
        pass

    @yt_com_group.command("queue", aliases=["q"])
    async def queue_command(self, ctx: commands.Context, *args):
        self.text_channels[ctx.guild] = ctx.channel
        if len(args) < 1:
            await ctx.send("No YouTube URL to use")
            return
        if ctx.author.voice is None:
            await ctx.send("You aren't currently in a voice channel.")
            return
        print("getting info")
        info = self.yt.extract_info(args[0], process=False, download=False)
        print("got info")
        video = self.yt.process_ie_result(info, download=False)
        format = list(self.selector(video))
        if "uploader" in info:
            title = f"{info['title']} - {info['uploader']}"
        else:
            title = f"{info['title']} - {info['webpage_url_domain']}"
        audio_file = AudioFile(format[0]["url"], volume=1, metadata={"guild": ctx.guild.id, "title": title,
                                                                     "url": info["webpage_url"]})
        if len(self.queue[ctx.guild]) > 0:
            await ctx.send(embeds=[nextcord.Embed(
                description=f"Queued: [{audio_file.metadata['title']}]({audio_file.metadata['url']})"
            )])
        self.queue[ctx.guild].append(audio_file)
        await self.sound_manager.queue(ctx.author, "music", audio_file, play_start=self.on_song_start, play_end=self.on_song_end)

    async def on_song_start(self, audio_file: AudioFile):
        guild = self.bot.get_guild(audio_file.metadata["guild"])
        guild_queue = self.queue[guild]
        while guild_queue[0] != audio_file:
            guild_queue.pop(0)
        await self.text_channels[guild].send(embeds=[nextcord.Embed(
            description=f"Now playing: [{audio_file.metadata['title']}]({audio_file.metadata['url']})"
        )])

    async def on_song_end(self, audio_file: AudioFile):
        guild = self.bot.get_guild(audio_file.metadata["guild"])
        guild_queue = self.queue[guild]
        if len(guild_queue) > 0:
            if guild_queue[0] == guild:
                guild_queue.pop(0)
        print("File finished, removing from queue")

    @yt_com_group.command("stop")
    async def stop_command(self, ctx: commands.Context, *args):
        self.queue.clear()
        await self.sound_manager.stop(ctx.author.guild, "music")
        await self.text_channels[guild].send(embeds=[nextcord.Embed(
            description="Stopped music playback."
        )])

    @yt_com_group.command("pause")
    async def pause_command(self, ctx: commands.Context, *args):
        self.text_channels[ctx.guild] = ctx.channel
        status = await self.sound_manager.is_paused(ctx.guild, "music")
        print("status", status)
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
        print("status", status)
        if status is None:
            await ctx.send("Nothing is currently queued.")
            return
        if await self.sound_manager.is_paused(ctx.guild, "music"):
            await self.sound_manager.play(ctx.author.guild, "music")
            await ctx.send("Playing...")
        else:
            await ctx.send("Already playing.")


def setup(bot):
    bot.add_cog(Youtube(bot))
