import nextcord
import nextcord.ext.commands as commands
import pytz
from random import choice
from datetime import datetime
import dateparser
import platform
from beatrice.util import member_to_mention, date_countdown
from nextcord_ormar import OrmarApp, AppModel
import ormar

MetaModel = OrmarApp.create_app("Schedule")


class AlarmModel(AppModel):
    class Meta(MetaModel):
        tablename = "schedule_alarms"

    id: int = ormar.Integer(primary_key=True)
    channel: int = ormar.BigInteger()
    time: datetime = ormar.DateTime()
    message: str = ormar.Text()


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

    # def __del__(self):
    #     if not self.timer.has_run:te
    #         self.timer.cancel()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Alarm({self.num}, {self.time}, {self.message})"


class Schedule(commands.Cog, name="manage_schedule"):
    def __init__(self, discord: commands.Bot):
        self.discord = discord
        self.alarms = {}
        self.timezone = pytz.timezone(self.discord.config["general"]["locale"])
        self._inited = False

    async def __async_init__(self):
        for alarm in await AlarmModel.objects.all():
            channel = self.discord.get_channel(alarm.channel)
            if channel is None:
                channel = await self.discord.create_dm(self.discord.get_user(alarm.channel))
            await self.add_alarm(alarm.id, alarm.time, alarm.message, channel)

    @commands.command("schedule", aliases=["sched"])
    async def add_alarm_cmd(self, ctx, time_string, *args):
        message = None
        user_mention = member_to_mention(ctx.author)
        if len(args) > 0:
            message = args[0]

        if message is None:
            templates = ["Ah, {}, your time is up I suppose.", "You can't keep sleeping forever {}, I suppose.", "{}, it's time."]
            message = choice(templates).format(user_mention)

        date = dateparser.parse(time_string, settings={'PREFER_DATES_FROM': 'future'})
        if date is None:
            await ctx.send("What? I don't know when that is!")
            return

        date = date.astimezone(self.timezone)

        channel_id = ctx.channel.id
        if isinstance(ctx.channel, nextcord.DMChannel):
            channel_id = ctx.author.id

        a_row = await AlarmModel.objects.create(channel=channel_id, time=date, message=message)
        await self.add_alarm(a_row.id, date, message, ctx.channel)

        templates = ["Very well, I set an alarm for {}.", "Why should I have to keep watch for you? ({})", "Hmmph! ({})"]

        fmt_string = "%B %-d at %-I:%M %p"
        if platform.system() == "Windows":  # Bruh
            fmt_string = "%B %d at %I:%M %p"
        date_string = f"{date.strftime(fmt_string)} {date_countdown(date)}"
        await ctx.send(choice(templates).format(date_string))

    async def add_alarm(self, id, date, message, channel):
        alarm = Alarm(self, id, date, message, channel)
        self.alarms[id] = alarm

    async def delete_alarm(self, id):
        del self.alarms[id]
        await AlarmModel.objects.filter(id=id).delete()


def setup(bot):
    bot.add_cog(Schedule(bot))
