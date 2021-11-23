import nextcord
from util.regex import MENTION_STRING


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


async def member_to_mention(self, member: nextcord.Member):
    return f"<@!{member.id}>"


async def get_user_name(self, user):
    if isinstance(user, nextcord.Member):
        return user.nick
    elif isinstance(user, nextcord.User):
        return user.name
    else:
        raise Exception("Unknown user type")
