import nextcord
import nextcord.ext.commands
from datetime import datetime, timedelta
from random import shuffle
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint


class NameRandomizer(nextcord.ext.commands.Cog):
    def __init__(self, discord, name_changer):
        self.discord = discord
        self.name_changer = name_changer

    async def get_names(self):
        users = set()
        for channel in self.discord.main_guild.text_channels:
            if channel.permissions_for(self.discord.main_guild.me).read_message_history:
                async for message in channel.history(limit=300, after=datetime.now() - timedelta(days=20)):
                    author = message.author
                    if isinstance(author, nextcord.User):
                        author = self.discord.main_guild.get_member(author.id)
                        if not author:
                            print("Was this user removed?", message.author)
                            continue
                    if author not in users and author:
                        users.add(author)
        users = list(users)
        pprint(users)

        user_names = self.name_changer(users)

        await self.reset_users()
        await self.save_users(users)

        for i, user in enumerate(users):
            try:
                await user.edit(nick=user_names[i])
            except Exception as e:
                print(e)
                print(f"Cannot change {user} to {user_names[i]}")
                dm = await user.create_dm()
                await dm.send(f"Hello! It's time for another round of nickname antics! Your new nickname is "
                              f"`{user_names[i]}`")
        print("Done!")

    async def reset_users(self):
        users = await self.load_users()
        for i, user in enumerate(users):
            try:
                await user.edit(nick=None)
            except:
                print("Couldn't reset", user)

    async def load_users(self):
        try:
            with open("users.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        users = []
        for i in data:
            users.append(self.guilds[0].get_member(i))
        return users

    async def save_users(self, users):
        data = []
        for i, user in enumerate(users):
            if user:
                data.append(user.id)
        with open("users.json", "w") as f:
            json.dump(data, f)


def shuffle_names(users):
    user_names = [user.name for user in users]
    shuffle(user_names)
    # Double check match ups
    has_matchup = True
    while has_matchup:
        has_matchup = False
        print("Checking matchups...")
        if users[0].name == user_names[0]:
            has_matchup = True
            a = user_names[len(user_names) - 1]
            user_names[len(user_names) - 1] = user_names[0]
            user_names[0] = a
        for i in range(1, len(users) - 1):
            if users[i].name == user_names[i]:
                has_matchup = True
                a = user_names[i - 1]
                user_names[i - 1] = user_names[i]
                user_names[i] = a
    return user_names


def long_names(users):
    user_names = []
    for user in users:
        name = user.name[:3]
        name += "".join([name[2] for i in range(5)])
        user_names.append(name)
    return user_names


async def ainput(prompt: str = "") -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)


def unscrambler(dictionary="words.json", add_letters=False, limit=5):
    async def function(users):
        from word_dictionary import Unscrambler
        u = Unscrambler(dictionary)
        new_names = []
        for user in users:
            name = user.name.lower()
            name = "".join([i for i in name if i in "abcdefghijklmnopqrstuvwxyz"])
            print("Searching", name)
            limit = min(max(int(round((26 * 12) * (1 / len(name)))), 1), 15)
            print("Use limit", limit)
            # limit = int(input())
            options = u.unscramble(name, add_letters=add_letters, limit=limit)
            print("User:", user, name, len(name))
            if options:
                for i, option in enumerate(options):
                    print(f"{i + 1}: {option}")
                print("Select an option")
                option = await ainput()
                new_names.append(options[int(option) - 1][0][0])
            else:
                print("No options available, type what you would like to use?")
                new_name = input()
                if len(new_name) > 0:
                    new_names.append(new_name)
                else:
                    new_names.append(user.name)

        return new_names

    return function
