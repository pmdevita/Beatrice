import nextcord
from nextcord.ext import commands
from yt_dlp import YoutubeDL
from beatrice.sound_manager import AudioFile, SoundManager


class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.yt = YoutubeDL({"quiet": True, "no_warnings": True})
        self.selector = self.yt.build_format_selector("ba/b")
        self.text_channels = {}
        self.sound_manager = None

    async def __async_init__(self):
        self.sound_manager: SoundManager = self.bot.cogs.get("SoundManager")

    def remember_channel(self, text_channel: nextcord.TextChannel):
        self.text_channels[text_channel.guild] = text_channel

    @commands.group("youtube", aliases=["yt"])
    async def yt_com_group(self, *args):
        pass

    @yt_com_group.command("play")
    async def play_command(self, ctx: commands.Context, *args):
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
        await self.sound_manager.play(ctx.author, "music", AudioFile(format[0]["url"], volume=1))

    @yt_com_group.command("stop")
    async def stop_command(self, ctx: commands.Context, *args):
        await self.sound_manager.stop(ctx.author.guild, "music")
        await ctx.send("Stopped music playback.")

    @yt_com_group.command("pause")
    async def pause_command(self, ctx: commands.Context, *args):
        status = await self.sound_manager.is_paused(ctx.guild, "music")
        if status is None:
            await ctx.send("Nothing is currently playing.")
            return
        if status:
            await self.sound_manager.pause(ctx.author.guild, "music")
            await ctx.send("Playback paused.")
        else:
            await ctx.send("Playback already paused.")

    async def unpause_command(self, ctx: commands.Context, *args):
        if not await self.sound_manager.is_paused(ctx.guild, "music"):
            await self.sound_manager.unpause(ctx.author.guild, "music")
            await ctx.send("Playing... (but not actually)")
        else:
            await ctx.send("Already playing.")


def setup(bot):
    bot.add_cog(Youtube(bot))
