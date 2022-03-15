import nextcord.ext.commands as commands
from random import choice
from beatrice.util import find_mentions, member_to_mention
from beatrice.sound_manager import AudioFile

HI_FILES = [
    ("beatrice_hi1.opus", "You come in here without knocking? What a rude one you are."),
    ("beatrice_hi2.opus", "You're irritating me to death. Either stop it or get blown away."),
    ("beatrice_hi3.opus", "You come in here every day without even knocking. You truly have no manners whatsoever.")
]


class Basic(commands.Cog):
    def __init__(self, discord: commands.Bot):
        self.discord = discord
        self.connection = None
        self.sound_manager = None

    async def __async_init__(self):
        self.sound_manager = self.discord.cogs.get("SoundManager")

    @commands.command("hi", aliases=["hello", "hey", "howdy", "beatrice", "beako", "betty"])
    async def hello(self, ctx: commands.Context, *args):
        member = ctx.author
        mentions = await find_mentions(ctx.guild, args)
        if mentions:
            member = mentions[0]

        if member.voice is None or not self.sound_manager:
            templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {}, I guess.", "I'm busy right now {}, shoo, shoo!"]
            await ctx.send(choice(templates).format(member.display_name))
        else:
            line = choice(HI_FILES)
            await self.sound_manager.queue(member, "notifications",
                                           AudioFile(f"assets/{line[0]}", 2, duck=True, metadata={
                                               "text": line[1].format(member.display_name),
                                               "channel": ctx.channel.id
                                           }), play_start=self.hello_sound)

    async def hello_sound(self, audio_file: AudioFile):
        channel = self.discord.get_channel(audio_file.metadata["channel"])
        await channel.send(audio_file.metadata["text"])

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(f"Hey stop that! ({round(self.discord.latency * 1000)}ms)")

    @commands.command(name="ban")
    async def ban(self, ctx: commands.Context, *args):
        mentions = await find_mentions(ctx.guild, args)
        if mentions:
            member = mentions[0]
            video_url = "https://cdn.discordapp.com/attachments/651901952053084175/939772862301081680/beatriceban.mov"
            text = f"You're in big trouble {await member_to_mention(member)}, I suppose! {video_url}"
            # embed = nextcord.Embed(description=text,
            #                        url=video_url)
            await ctx.send(text)
        else:
            await ctx.send(f"Who?")

    @commands.command("inhale")
    async def inhale_a_car(self, ctx: commands.Context, *args):
        await self.sound_manager.queue(ctx.author, "notifications", AudioFile("assets/inhale_a_car.opus", 2, duck=True))

    @commands.command("mouthful")
    async def mouthful(self, ctx: commands.Context, *args):
        await self.sound_manager.queue(ctx.author, "notifications", AudioFile("assets/mouthful_mode.opus", 2, duck=True))

    # @commands.Cog.listener("on_message")
    # async def on_message(self, message: nextcord.Message, *arg):
    #     print("got message", message)


def setup(bot):
    bot.add_cog(Basic(bot))
