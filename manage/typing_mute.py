import datetime
import nextcord
import nextcord.ext.commands as commands
import nextcord.errors as nx_errors
from random import choice


class Mute:
    def __init__(self, discord, user: nextcord.Member, guild):
        self.discord = discord
        self.user = user
        self.timer = None
        self.guild = guild

    async def typing(self, time: datetime.datetime):
        if self.timer:
            if not self.timer.has_run:
                self.timer.cancel()
        self.timer = self.discord.timer.schedule_task(time + datetime.timedelta(seconds=8), self.unmute)
        try:
            await self.user.edit(mute=True)
        except nx_errors.Forbidden as e:
            print("Can't mute user", e, self.user)

    async def unmute(self):
        try:
            await self.user.edit(mute=False)
        except nx_errors.Forbidden as e:
            print("Can't unmute user", e, self.user)


class TypingMute(commands.Cog):
    def __init__(self, bot):
        self.discord = bot
        self.users = {}

    @commands.command("typingmute", aliases=["tm"])
    async def toggle_mute(self, context: commands.Context, *args):
        if context.author in self.users:
            await self.users[context.author].unmute()
            self.users.pop(context.author)
            await context.send(choice([f"Calmed down now haven't you {context.author.display_name}?",
                                       f"Learned your lesson, I suppose?",
                                       f"Finally, some peace and quiet!"]) + " (Typing mute off)")
        else:
            self.users[context.author] = Mute(self.discord, context.author, context.guild)
            await context.send(choice([f"Be quiet {context.author.display_name}!",
                                       f"I can hardly read with all this noise {context.author.display_name}!",
                                       f"You're too noisy {context.author.display_name}, I suppose!"]) + " (Typing mute on)")


    @commands.Cog.listener("on_typing")
    async def on_typing(self, channel, user, when):
        if user in self.users:
            print("Typing event!", channel, user, when)
            await self.users[user].typing(when)


def setup(bot):
    bot.add_cog(TypingMute(bot))
