import nextcord
from nextcord.ext import commands
import re
from ..util import member_to_mention

REGEX = re.compile("https://media\.discordapp\.net([/.\w-]+\.(?:mp4|webm|mov))")


class MediaToCDN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message: nextcord.Message, *args):
        matches = REGEX.findall(message.content)
        if matches:
            await message.channel.send(f"{await member_to_mention(message.author)} You used media.discordapp.net instead "
                                       f"of cdn.discordapp.com ya idiot https://cdn.discordapp.com{matches[0]}")


def setup(bot):
    bot.add_cog(MediaToCDN(bot))

