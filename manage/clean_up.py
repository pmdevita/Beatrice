import nextcord
import nextcord.ext.commands
from datetime import datetime, timedelta
import re


class CleanUp(nextcord.ext.commands.Cog):
    def __init__(self, discord):
        self.discord = discord

    async def __async_init__(self):
        midnight = datetime.now()
        midnight = midnight.replace(hour=0, minute=0, second=0)
        midnight += timedelta(days=1)
        self.timer = self.discord.timer.schedule_task(midnight, self.clean_up, timedelta(days=1))

    async def clean_up(self, *args):
        print("Cleaning up channels...")
        YOUTUBE_REGEX = re.compile("(https?://youtube.com)")
        users = self.discord.config.getlist("clean_up", "users")
        for user in users:
            name, discriminator = user.split(":")
            for channel in self.discord.main_guild.text_channels:
                if channel.permissions_for(self.discord.main_guild.me).read_message_history:
                    async for message in channel.history(limit=1000, before=datetime.now() - timedelta(days=3),
                                                         after=datetime.now() - timedelta(days=30)):
                        author = message.author
                        if isinstance(author, nextcord.User):
                            author = self.discord.main_guild.get_member(author.id)
                            if not author:
                                print("Was this user removed?", message.author)
                                continue
                        if message.author.name != name or message.author.discriminator != discriminator:
                            continue
                        match = YOUTUBE_REGEX.match(message.content)
                        if match:
                            await message.delete()
        print("Clean up complete")


def setup(bot):
    bot.add_cog(CleanUp(bot))
