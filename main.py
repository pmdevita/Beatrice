import asyncio

import nextcord
import nextcord.ext.commands as commands
import configparser
import argparse
import logging

import tortoise

from util import Utils
from util.timer import Timer
from util.cog_loader import CogLoader
from nextcord_tortoise import Bot as TortoiseBot
from nextcord_tortoise import attach_argparse_group
from settings import CONFIG as TORTOISE_CONFIG
import aiohttp

parser = argparse.ArgumentParser(description="Discord Bot")
attach_argparse_group(parser)

config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split("#")[0].split(',')
                                                                  if i.strip() != ""]})
with open("config.ini", "r", encoding="utf-8") as f:
    config.read_file(f)

intents = nextcord.Intents.default()
intents.members = True
intents.reactions = True

# extensions = config.getlist("general", "extensions")
TORTOISE_CONFIG["connections"]["default"] = config["general"]["db_url"]


class DiscordBot(TortoiseBot):
    def __init__(self, *args, **kwargs):
        self.config = config
        self.utils = Utils(self)
        self.timer = Timer(self)
        self.cog_manager = CogLoader(self, config["general"]["cogs"])
        super().__init__(*args, **kwargs)
        self._has_inited = False
        self._has_inited_cogs = False

    def configure(self):
        self.cog_manager.init_bot()

    async def on_connect(self):
        if not self._has_inited:
            self._has_inited = True
            self.session = aiohttp.ClientSession(headers={"User-Agent": self.config["general"]["user_agent"]})

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # self.main_guild = self.guilds[0]
        if not self._has_inited_cogs:
            self._has_inited_cogs = True
            for cog in self.cogs.values():
                if callable(getattr(cog, "__async_init__", None)):
                    await cog.__async_init__()

    async def on_close(self):
        print("Closing")
        await tortoise.Tortoise.close_connections()
        for cog in self.cogs.values():
            if callable(getattr(cog, "on_close", None)):
                await cog.on_close()

    async def on_message(self, message):
        await self.cog_manager.process_commands(message)

    def tortoise_loop(self, *args):
        try:
            self.loop.run_until_complete(self.start(*args))
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            self.loop.run_until_complete(self.on_close())
            self.loop.close()


if __name__ == '__main__':
    args = parser.parse_args()
    prefix = config['general']['prefix']
    prefix = prefix.replace("\"", "")
    client = DiscordBot(command_prefix=prefix, tortoise_config=TORTOISE_CONFIG, intents=intents)
    client.configure()
    if args.aerich:
        from nextcord_tortoise.aerich import run_aerich
        run_aerich(client, args)
    else:
        client.tortoise_loop(config["general"]["token"])
