import nextcord
from util.regex import MENTION_STRING
from datetime import datetime


class Utils:
    def __init__(self, discord):
        self.discord = discord

    async def find_mentions(self, string):
        if isinstance(string, str):
            string = string.split()
        members = []
        for i in string:
            mention = MENTION_STRING.findall(i)
            if mention:
                members.append(await self.discord.main_guild.fetch_member(mention[0]))
        return members


async def member_to_mention(member: nextcord.Member):
    return f"<@!{member.id}>"


async def get_user_name(user):
    if isinstance(user, nextcord.Member):
        return user.nick
    elif isinstance(user, nextcord.User):
        return user.name
    else:
        raise Exception("Unknown user type")


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
    message += "```"
    await send(message)
