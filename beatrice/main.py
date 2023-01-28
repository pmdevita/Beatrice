import nextcord
import configparser
import asyncio
import aiohttp
try:
    import uvloop
except ImportError:
    pass
else:
    print("Using uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from .util.timer import Timer
from .util.cog_loader import CogLoader
from .util.background_tasks import BackgroundTasks
from nextcord_ormar import Bot


config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split("#")[0].split(',')
                                                                  if i.strip() != ""]})
with open("config.ini", "r", encoding="utf-8") as f:
    config.read_file(f)

intents = nextcord.Intents.default()
intents.members = True
intents.reactions = True
intents.guilds = True
intents.message_content = True


class DiscordBot(BackgroundTasks, Bot):
    def __init__(self, *args, **kwargs):
        self.config = config
        self.cog_manager = CogLoader(self, config["general"]["cogs"])
        super().__init__(*args, **kwargs)
        self.timer = Timer(self)
        self._has_inited_cogs = False
        self.session: aiohttp.ClientSession = None
        self._rollout_delete_unknown = config["general"].get("allow_unknown_commands", "false").lower() == "true"

    def configure(self):
        self.cog_manager.init_bot()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # self.main_guild = self.guilds[0]
        if not self._has_inited_cogs:
            self._has_inited_cogs = True
            for cog in self.cogs.values():
                if callable(getattr(cog, "__async_init__", None)):
                    self.start_background_task(cog.__async_init__())

    async def on_message(self, message):
        await self.cog_manager.process_commands(message)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        if self.config["general"].get("debug", "False").lower() == "true":
            print("Enabling Beatrice Async Debug")
            self.loop.set_debug(True)
        self.session =  aiohttp.ClientSession(headers={"User-Agent": self.config["general"]["user_agent"]})
        await super().start(token, reconnect=reconnect)

    async def _close_session(self):
        try:
            await self.session.close()
        except AttributeError:
            pass

    async def close(self) -> None:
        self.add_listener(self._close_session, "on_close")
        await super().close()


prefix = config['general']['prefix']
prefix = prefix.replace("\"", "")
client = DiscordBot(command_prefix=prefix, database_url=config["general"]["db_url"], intents=intents)
client.configure()


def main():
    sm = client.cogs.get("SoundManager")
    if sm:
        sm.start_bot()
    client.run(config["general"]["token"])
    # print("Beatrice exited loop")


if __name__ == '__main__':
    main()
