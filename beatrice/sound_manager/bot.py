import asyncio
import traceback
from nextcord.ext import commands


# import logging
# logging.basicConfig(level=logging.INFO)


class SoundManagerBot(commands.Bot):
    def __init__(self, pipe, config):
        self.pipe = pipe
        self.config = config
        self._inited = False
        self._cancel = False
        self._read_event = asyncio.Event()
        self._read_loop = None
        super(SoundManagerBot, self).__init__(command_prefix="disabled")

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
            # print("client receiving...")
            if not self.pipe.poll():
                # print("but there was nothing for client")
                continue
            data = self.pipe.recv()
            if data["command"] == "exit":
                await self.on_close(False)
                break
            await self.process_command(data)
        print("Sound manager shutting down...")

    async def process_command(self, data):
        try:
            command = data.pop("command")
            func = getattr(self.manager, command)
            if func:
                asyncio.create_task(func(**data))
        except Exception as e:
            print(traceback.format_exc())

    async def send_command(self, data):
        asyncio.create_task(self._send_command(data))

    async def _send_command(self, data):
        self.pipe.send(data)

    async def on_message(self, message):
        pass

    async def on_close(self, cancel_read=True):
        self._cancel = True
        if cancel_read and self._read_loop:
            self._read_loop.cancel()
        await self.close()


def start_bot(config, pipe):
    bot = SoundManagerBot(pipe, config)
    bot.run(config["token"])
    print("Sound manager exited loop")
