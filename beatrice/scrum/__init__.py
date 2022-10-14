import nextcord
from nextcord.ext import commands
from .views import *
from .models import *
from datetime import datetime, date, timedelta

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from beatrice.main import DiscordBot


class Scrum(commands.Cog):
    def __init__(self, bot: 'DiscordBot'):
        self.bot = bot
        self.interactions = []

    async def __async_init__(self):
        morning_start = datetime.now().replace(hour=9, minute=0, second=0)
        self.bot.timer.schedule_task(morning_start, self.create_day_posts, repeat=timedelta(hours=24))

    @commands.group("scrum")
    async def scrum_group(self, *args):
        pass

    async def should_scrum_today(self, day: date):
        # No weekends
        if day.weekday() > 5:
            return False
        return True

    async def create_day_posts(self):
        # Stop any previous day views and remove them
        while len(self.interactions):
            await self.interactions.pop(0).stop()

        day = date.today()
        # prefetch_related("days__day").
        guilds = await ScrumGuild.objects.all()
        print(guilds)
        for guild in guilds:
            scrum_day = await ScrumDay.objects.get_or_none(guild=guild, day=day)
            channel = self.bot.get_channel(guild.channel)
            assert isinstance(channel, nextcord.TextChannel)
            if scrum_day:
                if scrum_day.ignored:
                    continue
                if scrum_day.post_id:
                    try:
                        message = await channel.fetch_message(scrum_day.post_id)
                        await message.delete()
                    except nextcord.errors.NotFound:
                        pass
                    await scrum_day.update(post_id=None)
            await self.send_scrum_day_view(channel)

    @scrum_group.command("add")
    async def add_guild_command(self, ctx: commands.Context):
        await ScrumGuild.objects.create(guild=ctx.guild.id, channel=ctx.channel.id)
        await ctx.reply("Channel added to Scrum")
        await self.send_scrum_day_view(ctx.channel)

    @scrum_group.command("delete", aliases=["remove", "unsubscribe", "del", "unsub"])
    async def remove_server_command(self, ctx: commands.Context):
        await ScrumGuild.objects.delete(guild=ctx.guild.id, channel=ctx.channel.id)
        await ctx.reply("Channel removed from Scrum")

    async def send_scrum_day_view(self, channel: nextcord.TextChannel):
        entry = await ScrumDay.objects.get_or_none(day=date.today(), guild=channel.guild.id)
        if entry is None:
            entry = await ScrumDay.objects.create(day=date.today(), guild=channel.guild.id)
        print(entry)
        message, view = await ScrumDayView.send(channel, entry)
        await entry.update(post_id=message.id)
        self.interactions.append(view)


def setup(bot):
    bot.add_cog(Scrum(bot))

