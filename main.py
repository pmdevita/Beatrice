import nextcord as discord
import nextcord.ext.commands as commands
import configparser
import logging

from util import Utils

config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split("#")[0].split(',')]})
config.read("config.ini")

intents = discord.Intents.default()
intents.members = True

extensions = config.getlist("general", "extensions")


class DiscordBot(commands.Bot):
    async def on_ready(self):
        self.config = config
        self.utils = Utils(self)
        print(f"Logged in as {self.user}")
        self.main_guild = self.guilds[0]

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     print(f"Message from {message.author}: {message.content}")


if __name__ == '__main__':
    client = DiscordBot(command_prefix="-b ", intents=intents)

    for extension in extensions:
        client.load_extension(extension)

    client.run(config["general"]["token"])
