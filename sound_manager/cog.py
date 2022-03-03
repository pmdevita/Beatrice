import asyncio
import traceback

import nextcord
from nextcord import FFmpegPCMAudio
from nextcord.ext import commands
import numpy as np


class SoundManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = {}

    async def play(self, voice_channel: int, audio_channel: str, audio_file: str, override=False):
        voice_channel = self.bot.get_channel(voice_channel)
        guild = voice_channel.guild

        if guild not in self.guilds:
            self.guilds[guild] = GuildAudio(guild, self.bot.config)

        guild_manager = self.guilds[guild]
        await guild_manager.play_file(voice_channel, audio_channel, audio_file, override)


class GuildAudio(nextcord.AudioSource):
    def __init__(self, guild: nextcord.Guild, config):
        self.guild = guild
        self.config = config
        self.connection = None
        self.channel = None
        self.channels = {}
        for channel in self.config["channels"]:
            self.channels[channel] = AudioChannel(self)

        self.playing_task = None
        self._playing = False

    async def play_file(self, voice_channel: nextcord.VoiceChannel, audio_channel: str, audio_file: str, override=False):
        audio_channel = self.channels[audio_channel]
        audio_channel.play(audio_file, override)
        print("queueing file", self.connection)
        if not self.playing_task:
            print("opening connection")
            self.playing_task = asyncio.ensure_future(self.play_job(voice_channel))

    async def play_job(self, voice_channel: nextcord.VoiceChannel):
        print("starting play job")
        try:
            if self.connection:
                await self.connection.disconnect()
            self.channel = voice_channel
            try:
                self.connection = await voice_channel.connect()
            except nextcord.errors.ClientException:
                print("already connected??????")
            is_playing = asyncio.Event()
            while self.is_playing:
                self.connection.play(self, after=lambda x: is_playing.set())
                await is_playing.wait()
                is_playing.clear()
                print("playing finished, retrying?")
            print("stopping play job")
            await self.connection.disconnect()
            self.channel = None
            self.connection = None
        except:
            print(traceback.format_exc())
        self.playing_task = None

    @property
    def is_playing(self):
        return self._playing

    def _update_play(self):
        for channel in self.channels.values():
            if channel.is_playing():
                self._playing = True
                return
        self._playing = False

    def read(self) -> bytes:
        data = []
        for channel in self.channels.values():
            channel_data = channel.read()
            if channel_data:
                data.append(np.frombuffer(channel_data, np.int16))
        if not data:
            return bytes(0)
        if len(data) == 1:
            final = data[0]
        else:
            final = np.concatenate(data, axis=1)
            print("rendering", final)
            final = np.add.reduce(final, 0)
        return final.tobytes()


class AudioChannel(nextcord.AudioSource):
    def __init__(self, guild: GuildAudio):
        self.guild = guild
        self.queue = []
        self.source = None

    def play(self, audio_file: str, override=False):
        if override and len(self.queue) > 0:
            self.queue.insert(1, audio_file)
            self.next()
        else:
            self.queue.append(audio_file)
            self.start()
        print(self.queue)

    def is_playing(self):
        if self.source:
            return True
        else:
            return False

    def start(self):
        if self.queue:
            if not self.source:  # If we are already playing, don't just override it
                self.source = FFmpegPCMAudio(self.queue[0])
        else:
            self.source = None
        self.guild._update_play()

    def next(self):
        self.queue.pop(0)
        self.source = None
        self.start()

    def read(self) -> bytes:
        if self.source:
            data = self.source.read()
            if data:
                return data
            else:
                self.next()
        return bytes(0)


def setup(bot):
    bot.add_cog(SoundManagerCog(bot))
