import datetime
import nextcord
import nextcord.ext.commands as commands
import nextcord.errors as nx_errors


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
        self.timer = self.discord.timer.schedule_task(time + datetime.timedelta(seconds=8), self.check_typing)
        try:
            await self.user.edit(mute=True)
        except nx_errors.Forbidden as e:
            print("Can't mute user", e, self.user)

    async def check_typing(self):
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
            self.users.pop(context.author)
            await context.send("Mute toggled off.")
        else:
            self.users[context.author] = Mute(self.discord, context.author, context.guild)
            await context.send("Mute toggled on.")


    @commands.Cog.listener("on_typing")
    async def on_typing(self, channel, user, when):
        if user in self.users:
            print("Typing event!", channel, user, when)
            await self.users[user].typing(when)


def setup(bot):
    bot.add_cog(TypingMute(bot))
