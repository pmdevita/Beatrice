import nextcord
from beatrice.util.regex import MENTION_STRING, CHANNEL_STRING
from datetime import datetime, timedelta


class Utils:
    def __init__(self, discord):
        self.discord = discord


# Todo: fix for strings with multiple mentions not separated by spaces
async def find_mentions(guild: nextcord.Guild, string):
    if isinstance(string, list) or isinstance(string, tuple):
        string = " ".join(string)
    members = []
    mention = MENTION_STRING.findall(string)
    if mention:
        for i in mention:
            members.append(await guild.fetch_member(i))
    return members


async def find_channels(bot: nextcord.Client, string):
    if isinstance(string, list) or isinstance(string, tuple):
        string = " ".join(string)
    members = []
    mention = CHANNEL_STRING.findall(string)
    if mention:
        for i in mention:
            members.append(bot.get_channel(int(i)))
    return members


async def get_recent_users(guild, days=20):
    users = set()
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).read_message_history:
            async for message in channel.history(limit=300, after=datetime.now() - timedelta(days=days)):
                author = message.author
                if isinstance(author, nextcord.User):
                    author = guild.get_member(author.id)
                    if not author:
                        continue
                if author:
                    users.add(author)
    return list(users)


async def member_to_mention(member: nextcord.Member):
    return f"<@!{member.id}>"


def date_countdown(date: datetime):
    return f"<t:{round(date.timestamp())}:R>"


async def send_list(send, data_list):
    message = "```\n"
    column_counter = 0
    row = ""
    for key in data_list:
        if column_counter > 0:
            row += "    "
        if len(row) + len(key) > 42:
            column_counter = 0
            message += row + "\n"
            row = ""
        row += f"{key}"
        column_counter += 1
        if len(message) > 1950:
            column_counter = 0
            message += row + "\n"
            row = ""
        if len(message) > 1900:
            message += "```"
            await send(message)
            message = "```\n"
    message += row
    message += "```"
    await send(message)
