import asyncio
import re
import typing

import nextcord
import nextcord.ext.commands as commands
from random import choice
from beatrice.util import member_to_mention
from beatrice.util.slash_compat import Cog, command
from beatrice.sound_manager import AudioFile, SoundManager

HI_FILES = [
    ("beatrice_hi1.opus", "You come in here without knocking? What a rude one you are."),
    ("beatrice_hi2.opus", "You're irritating me to death. Either stop it or get blown away."),
    ("beatrice_hi3.opus", "You come in here every day without even knocking. You truly have no manners whatsoever.")
]

DIABETES = re.compile("my family history has (\w+)", re.I)
SOCK_DRAWER = re.compile("there\'?s nothing happening", re.I)


class Basic(Cog):
    def __init__(self, discord: commands.Bot):
        self.discord = discord
        self.connection = None
        self.sound_manager: typing.Optional[SoundManager] = None

    async def __async_init__(self):
        self.sound_manager = self.discord.cogs.get("SoundManager")

    @command("hi", aliases=["hello", "hey", "howdy", "beatrice", "beako", "betty"])
    @nextcord.slash_command("hi", description="Beatrice says hi")
    async def hello(self, interaction: nextcord.Interaction, member: typing.Optional[nextcord.Member] = None):
        member = member if member else interaction.user

        if isinstance(member, nextcord.Member):
            if member.voice and self.sound_manager:
                line = choice(HI_FILES)
                await self.sound_manager.queue(member, "notifications",
                                               AudioFile(f"assets/{line[0]}", 2, duck=True, metadata={
                                                   "text": line[1].format(member.display_name),
                                                   "channel": interaction.channel.id
                                               }), play_start=self.hello_sound)
                return
        templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {}, I guess.", "I'm busy right now {}, shoo, shoo!"]
        await interaction.send(choice(templates).format(member.display_name))

    async def hello_sound(self, audio_file: AudioFile):
        channel = self.discord.get_channel(audio_file.metadata["channel"])
        await channel.send(audio_file.metadata["text"])

    @command("ping")
    @nextcord.slash_command("ping")
    async def ping(self, ctx: nextcord.Interaction):
        """Get the bot's current websocket latency."""
        await ctx.send(f"Hey stop that! ({round(self.discord.latency * 1000)}ms)")

    @command("ban")
    @nextcord.slash_command("ban")
    async def ban(self, ctx: nextcord.Interaction, member: typing.Optional[nextcord.Member]):
        if not member:
            await ctx.send(f"Who?")
            return
        text = f"You're in big trouble {member_to_mention(member)}, I suppose!"
        video_url = "https://cdn.discordapp.com/attachments/984306454133637170/984318182477152306/beatriceban.mov"
        # embed = nextcord.Embed(description=text,
        #                        url=video_url)
        await ctx.send(text)
        # Might not work if perms missing
        try:
            await ctx.channel.send(video_url)
        except:
            await ctx.send(video_url)

    @nextcord.slash_command("inhale", description="INHALE A CAR")
    async def inhale_a_car(self, ctx: nextcord.Interaction):
        if self.sound_manager:
            await self.sound_manager.queue(ctx.user, "notifications",
                                           AudioFile("assets/inhale_a_car.opus", 2, duck=True))

    @nextcord.slash_command("mouthful", description="MoOOUTHFULLL MOOODDDEEEE")
    async def mouthful(self, ctx: nextcord.Interaction):
        if self.sound_manager:
            await self.sound_manager.queue(ctx.user, "notifications",
                                           AudioFile("assets/mouthful_mode.opus", 2, duck=True))

    @commands.Cog.listener("on_message")
    async def on_message(self, message: nextcord.Message, *arg):
        result = DIABETES.findall(message.content)
        if result:
            await message.channel.send(f"(There is {result[0].lower()} in my family history)")
        else:
            result = SOCK_DRAWER.findall(message.content)
            if result:
                await asyncio.sleep(3)
                await message.channel.send("I finally got the wildfire in my sock drawer under control!")


def setup(bot):
    bot.add_cog(Basic(bot))
