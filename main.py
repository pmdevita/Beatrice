import nextcord
import nextcord.ext.commands as commands
import configparser
import argparse
import logging
from util import Utils
from util.timer import Timer
from nextcord_tortoise import Bot as TortoiseBot
from nextcord_tortoise import attach_argparse_group
from settings import CONFIG as TORTOISE_CONFIG
import aiohttp

parser = argparse.ArgumentParser(description="Discord Bot")
attach_argparse_group(parser)

config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split("#")[0].split(',')
                                                                  if i.strip() != ""]})
config.read("config.ini")

intents = nextcord.Intents.default()
intents.members = True

extensions = config.getlist("general", "extensions")
TORTOISE_CONFIG["connections"]["default"] = config["general"]["db_url"]


class DiscordBot(TortoiseBot):
    def __init__(self, *args, **kwargs):
        self.config = config
        self.utils = Utils(self)
        self.timer = Timer(self)
        super().__init__(*args, **kwargs)
        self._has_inited = False

    def configure(self, extensions):
        for extension in extensions:
            self.load_extension(extension)

    async def on_connect(self):
        if not self._has_inited:
            self._has_inited = True
            self.session = aiohttp.ClientSession(headers={"User-Agent": self.config["general"]["user_agent"]})

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        self.main_guild = self.guilds[0]

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     print(f"Message from {message.author}: {message.content}")


if __name__ == '__main__':
    args = parser.parse_args()
    client = DiscordBot(command_prefix="-b ", tortoise_config=TORTOISE_CONFIG, intents=intents)

    client.configure(extensions)
    if args.aerich:
        from nextcord_tortoise.aerich import run_aerich
        run_aerich(client, args)
    else:
        client.run(config["general"]["token"])
        print("Exiting...")
        exit(0)
