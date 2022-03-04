from nextcord.ext import commands
from yt_dlp import YoutubeDL
from beatrice.sound_manager import AudioFile


class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.yt = YoutubeDL({"quiet": True, "no_warnings": True})
        self.selector = self.yt.build_format_selector("ba/b")

    async def __async_init__(self):
        self.sound_manager = self.bot.cogs["SoundManager"]

    @commands.group("youtube", aliases=["yt"])
    async def yt_com_group(self, *args):
        pass

    @yt_com_group.command("play")
    async def play_command(self, ctx: commands.Context, *args):
        if len(args) < 1:
            await ctx.send("No YouTube URL to use")
        print("getting info")
        info = self.yt.extract_info(args[0], process=False, download=False)
        print("got info")
        video = self.yt.process_ie_result(info, download=False)
        format = list(self.selector(video))
        await self.sound_manager.play(ctx.author, "music", AudioFile(format[0]["url"], volume=0.8))


def setup(bot):
    bot.add_cog(Youtube(bot))
