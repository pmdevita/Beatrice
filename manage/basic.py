import asyncio

import nextcord
import nextcord.ext.commands as commands
from nextcord import FFmpegOpusAudio
from random import choice
from util import find_mentions, member_to_mention

HI_FILES = [
    ("beatrice_hi1.opus", "You come in here without knocking? What a rude one you are."),
    ("beatrice_hi2.opus", "You're irritating me to death. Either stop it or get blown away."),
    ("beatrice_hi3.opus", "You come in here every day without even knocking. You truly have no manners whatsoever.")
]


class Basic(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.connection = None

    @commands.command("hi", aliases=["hello", "hey", "howdy", "beatrice", "beako", "betty"])
    async def hello(self, ctx: commands.Context, *args):
        member = ctx.author
        mentions = await find_mentions(ctx.guild, args)
        if mentions:
            member = mentions[0]

        if member.voice is None:
            templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {}, I guess.", "I'm busy right now {}, shoo, shoo!"]
            await ctx.send(choice(templates).format(member.display_name))
        else:
            line = choice(HI_FILES)
            await ctx.send(line[1].format(member.display_name))
            await self.soundboard(member, f"assets/{line[0]}")

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
        await self.soundboard(ctx.author, "assets/inhale_a_car.opus")

    @commands.command("mouthful")
    async def mouthful(self, ctx: commands.Context, *args):
        await self.soundboard(ctx.author, "assets/mouthful_mode.opus")

    async def soundboard(self, member: nextcord.Member, file_path):
        if member.voice is None:
            return

        connection = await member.voice.channel.connect()
        connection.play(FFmpegOpusAudio(file_path))
        while connection.is_playing():
            await asyncio.sleep(1)
        await connection.disconnect()


    # @commands.Cog.listener("on_message")
    # async def on_message(self, message: nextcord.Message, *arg):
    #     print("got message", message)


def setup(bot):
    bot.add_cog(Basic(bot))
