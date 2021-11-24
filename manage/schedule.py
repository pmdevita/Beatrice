import nextcord
import nextcord.ext.commands as commands
import pytz
from random import choice
from datetime import datetime
import dateparser
import platform
from util import member_to_mention
from tortoise.models import Model
from tortoise import fields


class AlarmModel(Model):
    id = fields.IntField(pk=True)
    channel = fields.BigIntField()
    time = fields.DatetimeField()
    message = fields.TextField()

    class Meta:
        table = "schedule_alarms"


class Alarm:
    def __init__(self, schedule, num, time: datetime, message, channel):
        self.schedule = schedule
        self.num = num
        self.time = time
        self.message = message
        self.channel = channel
        self.timer = self.schedule.discord.timer.schedule_task(time, self.wake)

    async def wake(self, *args):
        await self.channel.send(self.message)
        await self.schedule.delete_alarm(self.num)

    def __del__(self):
        self.timer.cancel()


class Schedule(commands.Cog):
    def __init__(self, discord: commands.Bot):
        self.discord = discord
        self.alarms = {}
        self.timezone = pytz.timezone(self.discord.config["general"]["locale"])

    async def on_ready(self):
        async for alarm in AlarmModel.all():
            channel = self.discord.get_channel(alarm.channel)
            if channel is None:
                channel = await self.discord.create_dm(self.discord.get_user(alarm.channel))
            await self.add_alarm(alarm.id, alarm.time, alarm.message, channel)

    @commands.command("schedule", aliases=["sched"])
    async def add_alarm_cmd(self, ctx, time_string, *args):
        message = None
        user_mention = await member_to_mention(ctx.author)
        if len(args) > 0:
            message = args[0]

        if message is None:
            templates = ["Ah, {}, your time is up I suppose.", "You can't keep sleeping forever {}, I suppose.", "{}, it's time."]
            message = choice(templates).format(user_mention)

        date = dateparser.parse(time_string, settings={'PREFER_DATES_FROM': 'future'})
        date = date.astimezone(self.timezone)

        channel_id = ctx.channel.id
        if isinstance(ctx.channel, nextcord.DMChannel):
            channel_id = ctx.author.id

        a_row = await AlarmModel.create(channel=channel_id, time=date, message=message)
        await self.add_alarm(a_row.id, date, message, ctx.channel)

        templates = ["Very well, I set an alarm for {}.", "Why should I have to keep watch for you? ({})", "Hmmph! ({})"]

        fmt_string = "%B %-d at %-I:%M %p"
        if platform.system() == "Windows":  # Bruh
            fmt_string = "%B %d at %I:%M %p"
        await ctx.send(choice(templates).format(date.strftime(fmt_string)))

    async def add_alarm(self, id, date, message, channel):
        alarm = Alarm(self, id, date, message, channel)
        self.alarms[id] = alarm

    async def delete_alarm(self, id):
        del self.alarms[id]
        await AlarmModel.filter(id=id).delete()


def setup(bot):
    bot.db_config.add_models("manage_schedule", "manage.schedule")
    bot.add_cog(Schedule(bot))
