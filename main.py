import nextcord as discord
import nextcord.ext.commands as commands
import configparser
import argparse
import logging
from database import TortoiseConfig
from util import Utils
from util.timer import Timer
from tortoise import Tortoise
import aiohttp

parser = argparse.ArgumentParser(description="Discord Bot")
parser.add_argument("--aerich")
parser.add_argument("--app")
parser.add_argument("--delete", action="store_true")

config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split("#")[0].split(',')
                                                                  if i.strip() != ""]})
config.read("config.ini")

intents = discord.Intents.default()
intents.members = True

extensions = config.getlist("general", "extensions")


class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.config = config
        self.utils = Utils(self)
        self.timer = Timer(self)
        self.db_config = TortoiseConfig()
        self.db_config.add_connection(self.config["general"]["db_url"])
        super().__init__(*args, **kwargs)

    def configure(self, extensions):
        for extension in extensions:
            self.load_extension(extension)

    async def on_connect(self):
        await Tortoise.init(self.db_config.export())
        self.session = aiohttp.ClientSession(headers={"User-Agent": self.config["general"]["user_agent"]})

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        self.main_guild = self.guilds[0]

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     print(f"Message from {message.author}: {message.content}")


if __name__ == '__main__':
    args = parser.parse_args()
    client = DiscordBot(command_prefix="-b ", intents=intents)

    client.configure(extensions)
    if args.aerich:
        from database import aerich
        aerich.run_aerich(client.db_config, args)
    else:
        client.run(config["general"]["token"])
        print("Exiting...")
        exit(0)
