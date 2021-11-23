import nextcord
import nextcord.ext.commands as commands
from random import choice


class Basic(commands.Cog):
    def __init__(self, discord):
        self.discord = discord

    @commands.command("hi")
    async def hello(self, ctx, *, member: nextcord.Member = None):
        print("hi there")
        member = member or ctx.author

        templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {} I guess.", "I'm busy right now {}, shoo, shoo!"]

        await ctx.send(choice(templates).format(member))

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(f"Hey stop that! ({round(self.discord.latency * 1000)}ms)")  # It's now self.bot.latency


def setup(bot):
    bot.add_cog(Basic(bot))
