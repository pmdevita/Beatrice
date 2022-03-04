import asyncio
from settings import SOUND_CONFIG

import nextcord
from nextcord.ext import commands
from .bot import start_bot, start_bot_async
from .data import AudioFile
import multiprocessing
# import aiomultiprocess
# import aioprocessing


class SoundManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self._cancel = False
        self._read_event = asyncio.Event()
        self._read_loop = None
        self.pipe, self.chpipe = multiprocessing.Pipe(True)
        bot_config = {
            "token": self.config["general"]["token"]
        }
        bot_config.update(SOUND_CONFIG)
        self.process = multiprocessing.Process(target=start_bot, args=(bot_config, self.chpipe))
        self.process.start()

    async def __async_init__(self):
        asyncio.get_event_loop().add_reader(self.pipe.fileno(), self._read_event.set)
        self._read_loop = asyncio.ensure_future(self._receiver())

    async def _receiver(self):
        while not self._cancel:
            if not self.pipe.poll():
                await self._read_event.wait()
            self._read_event.clear()
            # print("host receiving...")
            if not self.pipe.poll():
                # print("but there was nothing for host")
                continue
            data = self.pipe.recv()
            # print("host received")
            # print("Got data back in main process!", data)

    async def on_close(self):
        self._cancel = True
        if self._read_loop:
            self._read_loop.cancel()
        self.pipe.send({"command": "exit"})
        self.process.join()
        self.pipe.close()
        self.chpipe.close()

    async def play(self, voice_channel: nextcord.VoiceChannel, audio_channel, audio_file: AudioFile, override=False):
        """

        :param voice_channel: The voice channel to play the sound in or a person to track down to play to
        :param audio_channel: The audio channel to play the sound on
        :param override: Override the current sound in that channel. Otherwise, queue it to be played next
        :return:
        """
        if isinstance(voice_channel, nextcord.Member):
            if voice_channel.voice:
                voice_channel = voice_channel.voice.channel
            else:
                return

        command = {
            "command": "play",
            "voice_channel": voice_channel.id,
            "audio_channel": audio_channel,
            "audio_file": audio_file.as_dict(),
            "override": override
        }
        self.pipe.send(command)



    def __del__(self):
        self.on_close()


def setup(bot):
    bot.add_cog(SoundManager(bot))

