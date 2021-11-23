import nextcord.ext.commands as commands
from random import choice
from datetime import datetime, timedelta
from util.timer import Timer
import dateparser
import platform


class Alarm:
    def __init__(self, schedule, num, time: datetime, message, channel):
        self.schedule = schedule
        self.num = num
        self.time = time
        self.message = message
        self.channel = channel

        till_alarm = time - datetime.now()
        self.timer = Timer(0, "Alarm", self, self.wake,
                           initial_wait=till_alarm.total_seconds())

    async def wake(self, *args):
        await self.channel.send(self.message)
        self.schedule.delete_alarm(self.num)

    def __del__(self):
        self.timer.cancel()


class Schedule(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.alarms = {}
        self.counter = 0

    @commands.command("schedule", aliases=["sched"])
    async def add_alarm(self, ctx, time_string, *args):
        message = None
        user_mention = await self.discord.utils.member_to_mention(ctx.author)
        if len(args) > 0:
            message = args[0]

        if message is None:
            templates = ["Ah, {}, your time is up I suppose.", "You can't keep sleeping forever {}, I suppose.", "{}, it's time."]
            message = choice(templates).format(user_mention)

        date = dateparser.parse(time_string, settings={'PREFER_DATES_FROM': 'future'})

        alarm = Alarm(self, self.counter, date, message, ctx.channel)
        self.alarms[self.counter] = alarm
        self.counter += 1

        templates = ["Very well, I set an alarm for {}.", "Why should I have to keep watch for you? ({})", "Hmmph! ({})"]

        fmt_string = "%B %-d at %-I:%M %p"
        if platform.system() == "Windows":  # Bruh
            fmt_string = "%B %d at %I:%M %p"
        await ctx.send(choice(templates).format(date.strftime(fmt_string)))

    def delete_alarm(self, num):
        del self.alarms[num]


def setup(bot):
    bot.add_cog(Schedule(bot))
