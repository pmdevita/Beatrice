import asyncio
import multiprocessing.connection
import traceback
from nextcord.ext import commands
from beatrice.util.background_tasks import BackgroundTasks
try:
    import uvloop
except ImportError:
    pass
else:
    print("Using uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# import logging
# logging.basicConfig(level=logging.INFO)


class SoundManagerBot(BackgroundTasks, commands.Bot):
    def __init__(self, pipe: multiprocessing.connection.Connection, config):
        self.pipe = pipe
        self.config = config
        self._inited = False
        self._cancel = False
        self._read_event = asyncio.Event()
        self._read_loop = None
        super().__init__(chunk_guilds_at_startup=False)

    async def on_message(self, message):
        pass

    async def on_ready(self):
        if not self._inited:
            print("Loaded Sound Manager")
            await self.__async_init__()
            self._inited = True

    async def __async_init__(self):
        asyncio.get_event_loop().add_reader(self.pipe.fileno(), self._read_event.set)
        self._read_loop = asyncio.ensure_future(self._receiver())
        self.load_extension("beatrice.sound_manager.cog")
        self.manager = self.cogs["SoundManagerCog"]

    async def _receiver(self):
        while not self._cancel:
            if not self.pipe.poll():
                await self._read_event.wait()
            self._read_event.clear()
            if not self.pipe.poll():
                continue
            data = self.pipe.recv()
            if data["command"] == "exit":
                asyncio.ensure_future(self.close())
                break
            self.start_background_task(self.process_command(data))
        print("Sound manager shutting down...")

    async def process_command(self, data):
            command = data.pop("command")
            func = getattr(self.manager, command)
            if func:
                try:
                    await func(**data)
                except Exception:
                    print(traceback.format_exc())

    async def send_command(self, data):
        self.start_background_task(self._send_command(data))

    async def _send_command(self, data):
        self.pipe.send(data)

    async def on_message(self, message):
        pass

    async def on_close(self, cancel_read=True):
        self._cancel = True
        if cancel_read and self._read_loop:
            self._read_loop.cancel()
        try:
            await self.manager.close()
        except:
            print(traceback.format_exc())

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        if self.config.get("debug", "False").lower() == "true":
            print("Enabling SM Async Debug")
            self.loop.set_debug(True)
            self.loop.slow_callback_duration = 0.010
        await super().start(token, reconnect=reconnect)


def start_bot(config, pipe):
    try:
        bot = SoundManagerBot(pipe, config)
        bot.run(config["token"])
        print("Sound manager exited loop")
    except:
        print(traceback.format_exc())

