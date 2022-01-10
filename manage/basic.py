import nextcord.ext.commands as commands
from random import choice
from util import get_user_name, find_mentions


class Basic(commands.Cog):
    def __init__(self, discord):
        self.discord = discord

    @commands.command("hi", aliases=["hello", "hey", "howdy", "beatrice", "beako", "betty"])
    async def hello(self, ctx: commands.Context, *args):
        member = ctx.author
        mentions = find_mentions(ctx.guild, args)
        if mentions:
            member = mentions[0]

        templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {} I guess.", "I'm busy right now {}, shoo, shoo!"]
        await ctx.send(choice(templates).format(await get_user_name(member)))

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(f"Hey stop that! ({round(self.discord.latency * 1000)}ms)")


def setup(bot):
    bot.add_cog(Basic(bot))
