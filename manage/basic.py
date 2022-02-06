import nextcord.ext.commands as commands
import nextcord
from random import choice
from util import get_user_name, find_mentions, member_to_mention


class Basic(commands.Cog):
    def __init__(self, discord):
        self.discord = discord

    @commands.command("hi", aliases=["hello", "hey", "howdy", "beatrice", "beako", "betty"])
    async def hello(self, ctx: commands.Context, *args):
        member = ctx.author
        mentions = await find_mentions(ctx.guild, args)
        if mentions:
            member = mentions[0]

        templates = ["Hmmmmm... hi {}.", "Yes, yes, hello {}.", "Hi {}, I guess.", "I'm busy right now {}, shoo, shoo!"]
        await ctx.send(choice(templates).format(await get_user_name(member)))

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


def setup(bot):
    bot.add_cog(Basic(bot))
