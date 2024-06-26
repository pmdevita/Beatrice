import asyncio
import traceback
import typing

from beatrice.settings import SOUND_CONFIG

import nextcord
from nextcord.ext import commands
from .bot import start_bot
from .data import AudioFile
import multiprocessing

from ..util.background_tasks import BackgroundTasks


class SoundManager(commands.Cog, BackgroundTasks):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self._id_counter = 0
        self._func_counter = 0
        self.bot = bot
        self.config = self.bot.config
        self._cancel = False
        self._read_event = asyncio.Event()
        self._read_loop = None
        self.pipe, self.chpipe = multiprocessing.Pipe(True)
        self.bot_config = {
            "token": self.config["general"]["token"]
        }
        self.bot_config.update(SOUND_CONFIG)
        config = self.config["sound_manager"]
        if config:
            self.bot_config.update(dict(config))
        self.play_start_callbacks = {}
        self.play_end_callbacks = {}
        self.pause_callbacks = {}
        self.pause_channel_callbacks = {}
        self.stop_callbacks = {}
        self.func_callbacks = {}

    @property
    def _callback_id(self):
        temp = self._func_counter
        self._func_counter += 1
        return temp

    def start_bot(self):
        multiprocessing.set_start_method("spawn")
        self.process = multiprocessing.Process(target=start_bot, args=(self.bot_config, self.chpipe))
        self.process.start()

    async def __async_init__(self):
        asyncio.get_event_loop().add_reader(self.pipe.fileno(), self._read_event.set)
        self._read_loop = asyncio.ensure_future(self._receiver())

    async def _receiver(self):
        while not self._cancel:
            if not self.pipe.poll():
                await self._read_event.wait()
            self._read_event.clear()
            if not self.pipe.poll():
                continue
            data = self.pipe.recv()
            self.start_background_task(self.process_command(data))

    async def process_command(self, command):
        try:
            if command["command"] == "play_start":
                callback = self.play_start_callbacks.get(command["id"])
                if callback:
                    func, audio_file = callback
                    await func(audio_file)
            if command["command"] == "play_end":
                callback = self.play_end_callbacks.get(command["id"])
                if callback:
                    func, audio_file = callback
                    await func(audio_file)
            if command["command"] == "pause_status":
                guild = self.bot.get_guild(command["guild"])
                callbacks = self.pause_callbacks.get(guild)
                if callbacks:
                    for func in callbacks:
                        await func(command["is_paused"])
            if command["command"] == "stop":
                guild = self.bot.get_guild(command["guild"])
                callbacks = self.pause_callbacks.get(guild)
                if callbacks:
                    for func in callbacks:
                        await func(command["is_paused"])
            if command["command"] == "is_paused":
                func = self.func_callbacks.pop(command["id"])
                func.set_result(command["status"])
        except:
            print(traceback.print_exc())

    @commands.Cog.listener("on_close")
    async def close_bot(self):
        self._cancel = True
        if self._read_loop:
            self._read_loop.cancel()
        self.pipe.send({"command": "exit"})
        self.process.join()
        self.pipe.close()
        self.chpipe.close()

    async def queue(self, voice_channel: typing.Union[nextcord.VoiceChannel, nextcord.Member], audio_channel: str, audio_file: AudioFile,
                    override=False, play_start=None, play_end=None):
        """

        :param audio_file: An instance of AudioFile describing what and how to play
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
        if play_start or play_end:
            audio_file._id = self._id_counter
            self._id_counter += 1
        if play_start:
            self.play_start_callbacks[audio_file._id] = (play_start, audio_file)
        if play_end:
            self.play_end_callbacks[audio_file._id] = (play_end, audio_file)
        command = {
            "command": "queue",
            "voice_channel": voice_channel.id,
            "audio_channel": audio_channel,
            "audio_file": audio_file.as_dict(),
            "override": override
        }
        self.pipe.send(command)

    async def play(self, guild: nextcord.Guild, audio_channel: str = None):
        command = {
            "command": "play",
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        self.pipe.send(command)

    async def pause(self, guild: nextcord.Guild, audio_channel: str = None):
        command = {
            "command": "pause",
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        self.pipe.send(command)

    async def unpause(self, guild: nextcord.Guild, audio_channel: str = None):
        command = {
            "command": "unpause",
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        self.pipe.send(command)

    async def stop(self, guild: nextcord.Guild, audio_channel: str = None):
        command = {
            "command": "stop",
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        self.pipe.send(command)

    async def is_paused(self, guild: nextcord.Guild, audio_channel: str = None):
        command = {
            "command": "is_paused",
            "id": self._func_counter,
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        future = self.bot.loop.create_future()
        self.func_callbacks[self._callback_id] = future
        self.pipe.send(command)
        return await future

    async def remove(self, guild: nextcord.Guild, audio_channel: str, audio_file: AudioFile):
        command = {
            "command": "remove",
            "guild": guild.id,
            "audio_file": audio_file.as_dict(),  # todo: apparently it just pickles stuff through the connection so
            "audio_channel": audio_channel       # this is unnecessary???
        }
        self.pipe.send(command)

    async def next(self, guild: nextcord.Guild, audio_channel: str):
        command = {
            "command": "next",
            "guild": guild.id,
            "audio_channel": audio_channel
        }
        self.pipe.send(command)

    async def sticky_voicechannel(self, guild: nextcord.Guild, voice_channel: nextcord.VoiceChannel = None):
        command = {
            "command": "sticky_voicechannel",
            "guild": guild.id,
            "voice_channel": voice_channel.id if voice_channel else None
        }
        self.pipe.send(command)

    async def unsticky_voicechannel(self, guild: nextcord.Guild):
        command = {
            "command": "unsticky_voicechannel",
            "guild": guild.id
        }
        self.pipe.send(command)

    def __del__(self):
        pass
        # self.on_close()


def setup(bot):
    bot.add_cog(SoundManager(bot))

