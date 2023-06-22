import typing

import nextcord
import ormar
from nextcord.ext import commands
from datetime import datetime, timedelta

from nextcord_ormar import OrmarApp, AppModel

from beatrice.util import member_to_mention, channel_to_mention
from beatrice.util.background_tasks import BackgroundTasks
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from beatrice.main import DiscordBot

base_date = datetime(year=2000, month=1, day=1)
start = base_date.replace(hour=23, minute=45)
end = base_date.replace(day=2, hour=5, minute=0)


def should_check_sleep():
    time = datetime.now().replace(year=2000, month=1, day=1)
    # if increasing by a day still makes it behind the end time, do so
    # this fixes troubles with intervals between days
    if time < end and time.replace(day=2) < end:
        time = time.replace(day=2)
    return start < time < end


def get_check_time_start():
    return datetime.now().replace(hour=start.hour, minute=start.minute)


RESPONSES = [
    "Hey {members}, you should probably start winding down.",
    "{members} are you almost done?",
    "{members} OK party is over!",
    "Go to bed {members}. Go directly to bed. Do not check your phone. Do not respond to this message.",
    "Uhh... hey {members}, what are you still doing here?",
    "{members} I told you to go to sleep a while ago, what are you doing?",
    "I'm going to be very cross with you {members}!",
    "I'm not going to ask again {members}! Go to sleep!",
    "{members} SLEEP!"
]

MetaModel = OrmarApp.create_app("sleep")


class SleepChannel(AppModel):
    class Meta(MetaModel):
        pass

    guild = ormar.BigInteger(primary_key=True, autoincrement=False)
    channel = ormar.BigInteger(autoincrement=False)


class SleepCog(commands.Cog, BackgroundTasks):
    def __init__(self, bot: "DiscordBot"):
        super().__init__()
        self.bot = bot
        self.guilds = {}

    async def __async_init__(self):
        # If we are within the time interval, do a check now
        if should_check_sleep():
            self.start_background_task(self.check_servers())
        else:
            self.bot.timer.schedule_task(get_check_time_start(), self.check_servers)

    async def check_servers(self):
        guilds = await SleepChannel.objects.all()
        for sleep_channel in guilds:
            guild = self.bot.get_guild(sleep_channel.guild)
            members = set()
            for voice_channel in guild.voice_channels:
                if len(voice_channel.members) > 0:
                    members.update(voice_channel.members)
            if len(members) > 0:
                await self.yell_at_members(guild, list(members))
            elif guild in self.guilds:
                del self.guilds[guild]
        if should_check_sleep():
            self.bot.timer.schedule_task(datetime.now() + timedelta(minutes=5), self.check_servers)

    async def yell_at_members(self, guild: nextcord.Guild, members: typing.List[nextcord.Member]):
        channel_id = await SleepChannel.objects.get_or_none(guild=guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id.channel)
            summon_text = " ".join([member_to_mention(member) for member in members])
            if guild not in self.guilds:
                self.guilds[guild] = 0
            response = RESPONSES[self.guilds[guild]]
            await channel.send(response.format(members=summon_text))
            self.guilds[guild] = self.guilds[guild] + 1

    @commands.group("sleep")
    async def sleep_group(self, *args):
        pass

    @sleep_group.command("set")
    async def set_sleep_channel(self, ctx: commands.Context, channel: nextcord.TextChannel, *args):
        sleep_channel = await SleepChannel.objects.get_or_none(guild=ctx.guild.id)
        if sleep_channel:
            sleep_channel.channel = channel.id
            await sleep_channel.update()
        else:
            await SleepChannel.objects.create(guild=ctx.guild.id, channel=channel.id)
        await SleepChannel.objects.update_or_create(guild=ctx.guild.id, channel=channel.id)
        await ctx.send(f"Set sleep reminder channel to {channel_to_mention(channel)}")

    @sleep_group.command("unset")
    async def unset_sleep_channel(self, ctx: commands.Context, *args):
        await SleepChannel.objects.filter(guild=ctx.guild.id).delete()
        await ctx.send("Unset sleep channel")


def setup(bot):
    bot.add_cog(SleepCog(bot))
