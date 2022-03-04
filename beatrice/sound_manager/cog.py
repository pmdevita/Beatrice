import asyncio
import dataclasses
import time
import traceback

import nextcord
from nextcord import FFmpegPCMAudio, opus
from nextcord.ext import commands
import numpy as np
from .data import AudioFile


class SoundManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = {}
        self.playback_guilds = {}
        self.playback_task = None

    async def play(self, voice_channel: int, audio_channel: str, audio_file: dict, override=False):
        voice_channel = self.bot.get_channel(voice_channel)
        guild = voice_channel.guild
        audio_file = AudioFile(**audio_file)
        if guild not in self.guilds:
            self.guilds[guild] = GuildAudio(self, guild, self.bot.config)

        guild_manager = self.guilds[guild]
        await guild_manager.play_file(voice_channel, audio_channel, audio_file, override)

    async def register_playback(self, guild: 'GuildAudio', channel: nextcord.VoiceChannel):
        if guild not in self.playback_guilds:
            connection = await channel.connect()
            connection.encoder = opus.Encoder()
            self.playback_guilds[guild] = GuildConnection(guild, channel, connection)

        if not self.playback_task:
            self.playback_task = asyncio.ensure_future(self.playback())

    async def unregister_playback(self, guild):
        if guild in self.playback_guilds:
            await self.playback_guilds[guild].connection.disconnect()
            del self.playback_guilds[guild]

    async def playback(self):
        try:
            print("starting playback loop")
            total = 0
            count = 0
            loop_start = time.time()
            while True:
                if not self.playback_guilds:
                    print("ending loop")
                    break
                start = time.time()
                await asyncio.gather(*[i.send() for i in self.playback_guilds.values()])
                diff = time.time() - start
                total += diff
                count += 1
                avg = total / count
                total_offset = (count * 0.02) - (time.time() - loop_start)
                total_wait = max(0, round(0.02 - avg + total_offset, 3))
                if count % 250 == 0:
                    print("Avg time to render 20ms", avg, "current total offset", time.time() - loop_start, "waiting for", total_wait)
                if total_wait:
                    await asyncio.sleep(total_wait)
                if count > 9000:  # 50 * 60 * 3 minutes
                    total = avg
                    count = 1
                    loop_start = time.time()
        except:
            print(traceback.format_exc())
        self.playback_task = None


@dataclasses.dataclass
class GuildConnection:
    guild: 'GuildAudio'
    channel: nextcord.VoiceChannel
    connection: nextcord.VoiceClient = None

    async def send(self):
        data = await self.guild.read()
        if data:
            self.connection.send_audio_packet(data, encode=True)


class GuildAudio(nextcord.AudioSource):
    def __init__(self, manager: SoundManagerCog, guild: nextcord.Guild, config):
        self.manager = manager
        self.guild = guild
        self.config = config
        self.connection = None
        self.channel = None
        self.channels = {}
        self.dt = np.dtype("<h")
        self.dt_info = np.iinfo(np.int16)
        for channel in self.config["channels"]:
            self.channels[channel] = AudioChannel(self)

        self.playing_task = None
        self._playing = False
        self.keep_playing = asyncio.Event()
        self.duck_manager = DuckManager(self)

    async def play_file(self, voice_channel: nextcord.VoiceChannel, audio_channel: str, audio_file: AudioFile,
                        override=False):
        audio_channel = self.channels[audio_channel]
        await audio_channel.play(audio_file, override)
        print("queueing file", self.connection)
        await self.manager.register_playback(self, voice_channel)

    async def _update_play(self):
        for channel in self.channels.values():
            if channel.is_playing():
                self._playing = True
                return
        self._playing = False
        await self.manager.unregister_playback(self)

    async def read(self) -> bytes:
        try:
            awaitables = []
            data = []
            for channel in self.channels.values():
                awaitables.append(channel.read())
            await_data = await asyncio.gather(*awaitables)
            for channel_data in await_data:
                if channel_data:
                    data.append(np.frombuffer(channel_data, self.dt))
            if not data:
                return bytes(0)
            if len(data) == 1:
                final = data[0]
            else:
                final = np.stack(data)
                final = np.add.reduce(final, 0)
                final = np.clip(final, a_min=self.dt_info.min, a_max=self.dt_info.max)
                final = final.astype(np.int16)
            return final.tobytes()
        except:
            print(traceback.format_exc())


class DuckManager:
    def __init__(self, guild: GuildAudio):
        self.guild = guild
        self.duck_job = None
        self.waiting_to_play = None
        self.ducked = False

    def duck(self, main_channel):
        if self.duck_job:
            self.duck_job.cancel()
        self.duck_job = asyncio.ensure_future(self._duck(main_channel))

    async def _duck(self, main_channel):
        try:
            print("ducking....")
            next_event = asyncio.Event()
            main_channel.next_event = next_event
            self.waiting_to_play = main_channel
            events = []
            for channel in self.guild.channels.values():
                if channel == main_channel:
                    continue
                event = asyncio.Event()
                channel.duck(1, .3, .8, event=event)
                events.append(event)
            print(events)
            await asyncio.gather(*[i.wait() for i in events])
            print("finished ducking, playing")
            main_channel.pause = False
            # self.guild.keep_playing.set()
            await next_event.wait()
            print("finished playing, unducking")
            for channel in self.guild.channels.values():
                if channel == main_channel:
                    continue
                channel.duck(.3, 1, .5)
        except:
            print(traceback.format_exc())
        self.duck_job = None


class AudioChannel(nextcord.AudioSource):
    def __init__(self, guild: GuildAudio):
        self.guild = guild
        self.queue = []
        self.source = None
        self.file_volume = 1
        self.automation = None
        self.automation_event = None
        self.next_event = None
        self.pause = False

    def __repr__(self):
        return f"AudioChannel({self.source} {'paused' if self.pause else 'play'} {self.queue})"

    async def play(self, audio_file: AudioFile, override=False):
        if override and len(self.queue) > 0:
            self.queue.insert(1, audio_file)
            await self.next()
        else:
            self.queue.append(audio_file)
            await self.start()
        print(self.queue)

    def is_playing(self):
        if self.source:
            return True
        else:
            return False

    async def start(self, next_event=None, override=False):
        """

        :param next_event: Event to set once the next song is played
        :param override: Override the wait for ducking
        :return:
        """
        if self.queue:
            if not self.source:  # If we are already playing, don't just override it
                if self.queue[0].duck and not override:
                    self.guild.duck_manager.duck(self)
                    self.pause = True
                print("setting source")
                self.source = FFmpegPCMAudio(self.queue[0].file)
                self.file_volume = self.queue[0].volume
                if next_event:
                    self.next_event = next_event
        else:
            self.source = None
        await self.guild._update_play()

    async def next(self):
        if self.next_event:
            self.next_event.set()
            self.next_event = None
        self.queue.pop(0)
        self.source = None
        await self.start()

    def duck(self, from_target, to_target, seconds, event: asyncio.Event = None):
        self.automation_event = event
        if self.is_playing():
            self.automation = VolumeAutomation(self, from_target, to_target, seconds)
        else:
            self.automation_complete()

    def automation_complete(self):
        if self.automation_event:
            self.automation_event.set()
            self.automation_event = None

    async def read(self) -> bytes:
        if self.source and not self.pause:
            data = self.source.read()
            if data:
                arr = np.frombuffer(data, dtype=self.guild.dt)
                # print("before", arr)
                # arr = np.multiply(arr, .5, dtype=self.guild.dt, casting="unsafe")
                arr = arr * .5 * self.file_volume

                if self.automation:
                    if self.automation.is_automating():
                        automation = self.automation.next(len(arr))
                        combined = np.stack([arr, automation])
                        arr = np.multiply.reduce(combined, 0)
                    else:
                        arr = arr * self.automation.to_target
                arr = arr.astype(np.int16)
                return arr.tobytes()
            else:
                await self.next()
        return bytes(0)


class VolumeAutomation:
    def __init__(self, channel, from_target, to_target, seconds):
        self.channel = channel
        self.from_target = from_target
        self.to_target = to_target
        self.samples = seconds * 50 * 1920  # 1920 int16s for 20ms of audio, 50 per second
        self.current = 0

    def is_automating(self):
        return self.current < self.samples - 1

    def next(self, length):
        diff = self.to_target - self.from_target
        arr = np.fromfunction(lambda x: diff * ((x + self.current) / self.samples) + self.from_target, shape=(length,))
        self.current += length
        if not self.is_automating():
            print("automation complete")
            self.channel.automation_complete()
        return arr


def setup(bot):
    bot.add_cog(SoundManagerCog(bot))
