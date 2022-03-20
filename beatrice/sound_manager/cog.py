import asyncio
import concurrent.futures
import dataclasses
import time
import traceback
import typing

import nextcord
from nextcord.ext import commands
import numpy as np
from .data import AudioFile
from nextcord import FFmpegPCMAudio, opus

if not opus.is_loaded():
    print("loading opus...")
    opus._load_default()
    print("opus loaded")
from .source import AsyncFFmpegAudio, AsyncFFmpegPCMWrapper, AsyncVoiceClient, AsyncEncoder


class SoundManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guilds = {}
        self.playback_guilds = {}
        self.playback_task = None
        self.encode_thread_pool = concurrent.futures.ThreadPoolExecutor()
        # self.encode_thread_pool = concurrent.futures.ProcessPoolExecutor()
        if not opus.is_loaded():
            opus._load_default()

    async def queue(self, voice_channel: int, audio_channel: str, audio_file: dict, override=False):
        try:
            voice_channel = self.bot.get_channel(voice_channel)
            guild = voice_channel.guild
            audio_file = AudioFile(**audio_file)
            if guild not in self.guilds:
                self.guilds[guild] = GuildAudio(self, guild, self.bot.config)

            guild_manager = self.guilds[guild]
            await guild_manager.queue_file(voice_channel, audio_channel, audio_file, override)
        except:
            print(traceback.format_exc())

    async def play(self, guild: int, audio_channel: str = None):
        try:
            guild = self.bot.get_guild(guild)
            guild_manager = self.guilds.get(guild)
            await guild_manager.play(audio_channel)
        except:
            print(traceback.format_exc())

    async def pause(self, guild: int, audio_channel: str = None):
        try:
            guild = self.bot.get_guild(guild)
            guild_manager = self.guilds.get(guild)
            await guild_manager.pause(audio_channel)
        except:
            print(traceback.format_exc())

    async def stop(self, guild: int, audio_channel: str = None):
        try:
            guild = self.bot.get_guild(guild)
            guild_manager = self.guilds.get(guild)
            await guild_manager.stop(audio_channel)
        except:
            print(traceback.format_exc())

    async def register_playback(self, guild: 'GuildAudio', channel: nextcord.VoiceChannel):
        if guild not in self.playback_guilds:
            connection = await channel.connect(cls=AsyncVoiceClient)
            connection.encoder = AsyncEncoder(self.encode_thread_pool, self.bot.loop)
            # connection = None
            self.playback_guilds[guild] = GuildConnection(guild, channel, connection)

        if not self.playback_task:
            self.playback_task = asyncio.ensure_future(self.playback())

    async def unregister_playback(self, guild):
        if guild in self.playback_guilds:
            await self.playback_guilds[guild].connection.disconnect()
            del self.playback_guilds[guild]

    @commands.Cog.listener("on_voice_state_update")
    async def on_voice_state_update(self, member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
        guild = member.guild
        guild_manager = self.guilds.get(guild)
        if guild_manager:
            guild_connection = self.playback_guilds.get(guild_manager)
            if guild_connection:
                if after.channel == guild_connection.channel:
                    await guild_manager.pause()
                    await asyncio.sleep(1)
                    await guild_manager.play()

    async def playback(self):
        try:
            print("starting playback loop")
            count = 0
            avg = RollingAverage(500, 0)
            loop_start = time.time()
            while True:
                if not self.playback_guilds:
                    print("ending loop")
                    break
                start = time.time()
                await asyncio.gather(*[i.send() for i in self.playback_guilds.values()])
                diff = time.time() - start
                avg.add(diff)
                given_avg = avg.average()
                total_offset = (count * 0.02) - (time.time() - loop_start)
                total_wait = round(0.02 - given_avg + total_offset, 3)
                count += 1
                if count % 250 == 0:
                    print("Avg time to render 20ms", given_avg, "current total offset", time.time() - loop_start, "waiting for", total_wait)
                if total_wait > 0:
                    try:
                        await asyncio.sleep(total_wait)
                    except asyncio.exceptions.CancelledError:
                        break
                if count > 9000:  # 50 * 60 * 3 minutes
                    count = 1
                    loop_start = time.time()
        except:
            print(traceback.format_exc())
        self.playback_task = None

    async def play_start_callback(self, audio_file: AudioFile):
        if audio_file._id is not None:
            await self.bot.send_command({
                "command": "play_start",
                "id": audio_file._id
            })

    async def play_end_callback(self, audio_file: AudioFile):
        if audio_file._id is not None:
            await self.bot.send_command({
                "command": "play_end",
                "id": audio_file._id
            })

    async def pause_callback(self, is_paused: bool, guild: nextcord.Guild, channel: str):
        await self.bot.send_command({
            "command": "pause_status",
            "is_paused": is_paused,
            "guild": guild.id
        })

    async def stop_callback(self, guild: nextcord.Guild):
        await self.bot.send_command({
            "command": "stop",
            "guild": guild.id
        })

    async def is_paused(self, id: int, guild: int, audio_channel: str = None):
        guild = self.bot.get_guild(guild)
        command = {
            "command": "is_paused",
            "id": id,
            "status": None
        }
        guild_manager = self.guilds.get(guild)
        if guild_manager:
            if audio_channel:
                command["status"] = guild_manager.channels[audio_channel].pause
            else:
                command["status"] = guild_manager.is_paused
        await self.bot.send_command(command)

    async def remove(self, guild: int, audio_channel: str, audio_file: dict):
        guild = self.bot.get_guild(guild)
        audio_file = AudioFile(**audio_file)
        guild_manager = self.guilds.get(guild)
        if guild_manager:
            await guild_manager.remove(audio_channel, audio_file)

    async def next(self, guild: int, audio_channel: str):
        guild = self.bot.get_guild(guild)
        guild_manager = self.guilds.get(guild)
        if guild_manager:
            await guild_manager.next(audio_channel)


class RollingAverage:
    def __init__(self, size, weight):
        self.size = size
        self.weight = weight
        self.index = 0
        self.array = np.zeros(self.size, dtype=np.float)
        self.total = 0

    def add(self, value):
        self.array[self.index] = value
        self.index += 1
        if self.total < self.size:
            self.total += 1
        if self.index >= self.size:
            self.index = 0

    def average(self):
        return np.sum(self.array) / self.total


@dataclasses.dataclass
class GuildConnection:
    guild: 'GuildAudio'
    channel: nextcord.VoiceChannel
    connection: AsyncVoiceClient = None
    buffer: bytes = None

    async def prepare(self):
        data = await self.guild.read()
        self.buffer = await self.connection.encode()

    async def send(self):
        data = await self.guild.read()
        if data:
            try:
                await self.connection.send_audio_packet(data, encode=True)
            except OSError:
                print("Forcibly disconnected from", self.guild)
                await self.guild.stop()
                await self.guild.manager.unregister_playback(self.guild)


AUDIO_DATA_TYPE = np.dtype("<h")
AUDIO_DATA_TYPE_INFO = np.iinfo(np.int16)


class GuildAudio(nextcord.AudioSource):
    def __init__(self, manager: SoundManagerCog, guild: nextcord.Guild, config):
        self.manager = manager
        self._paused = False
        self.guild = guild
        self.config = config
        self.voice_channel = None
        self.channels = {}
        for channel in self.config["channels"]:
            self.channels[channel] = AudioChannel(self)

        self.playing_task = None
        self._playing = False
        self.keep_playing = asyncio.Event()
        self.duck_manager = DuckManager(self)

    async def stop(self, audio_channel: str = None):
        if audio_channel:
            self.channels[audio_channel].stop()
        else:
            for channel in self.channels.values():
                channel.stop()
        self._paused = False
        await self._update_play()

    async def queue_file(self, voice_channel: nextcord.VoiceChannel, audio_channel: str, audio_file: AudioFile,
                         override=False):
        audio_channel = self.channels[audio_channel]
        self.voice_channel = voice_channel
        await audio_channel.queue_file(audio_file, override)
        await self._update_play()

    async def play(self, audio_channel: str = None):
        if audio_channel:
            self.channels[audio_channel].pause = False
        else:
            self._paused = False
        await self._update_play()

    async def pause(self, audio_channel: str = None, unregister=True):
        if audio_channel:
            self.channels[audio_channel].pause = True
        else:
            self._paused = True
        await self._update_play(unregister=unregister)

    async def remove(self, audio_channel: str, audio_file: AudioFile):
        await self.channels[audio_channel].remove(audio_file)

    async def next(self, audio_channel: str):
        await self.channels[audio_channel].next()

    @property
    def is_paused(self):
        return self._paused

    async def _update_play(self, unregister=True):
        if not self._paused:
            for channel in self.channels.values():
                if channel.is_playing():
                    self._playing = True
                    await self.manager.register_playback(self, self.voice_channel)
                    return
        self._playing = False
        if unregister:
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
                    data.append(np.frombuffer(channel_data, AUDIO_DATA_TYPE))
            if not data:
                return bytes(0)
            if len(data) == 1:
                final = data[0]
            else:
                final = np.stack(data)
                final = np.add.reduce(final, 0)
                final = np.clip(final, a_min=AUDIO_DATA_TYPE_INFO.min, a_max=AUDIO_DATA_TYPE_INFO.max)
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
            # print("ducking....")
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
            # print(events)
            await asyncio.gather(*[i.wait() for i in events])
            # print("finished ducking, playing")
            await main_channel.play(next_event, override=True)
            await next_event.wait()
            # print("finished playing, unducking")
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
        self.source: AsyncFFmpegAudio = None
        self.file_volume = 1
        self.automation = None
        self.automation_event = None
        self.next_event = None
        self.pause = False

    def __repr__(self):
        return f"AudioChannel({self.source} {'paused' if self.pause else 'play'} {self.queue})"

    async def queue_file(self, audio_file: AudioFile, override=False):
        if override and len(self.queue) > 0:
            self.queue.insert(1, audio_file)
            await self.next()
        else:
            self.queue.append(audio_file)
            await self.play()

    def is_playing(self):
        if self.source:
            return not self.pause
        else:
            return False

    def stop(self):
        self.queue.clear()
        if self.source:
            self.source.close()
            self.source = None
        self.pause = False

    async def play(self, next_event=None, override=False):
        """

        :param next_event: Event to set once the next song is played
        :param override: Override the wait for ducking
        :return:
        """
        self.pause = False
        if self.queue:
            if not self.source:  # If we are already playing, don't just override it
                if self.queue[0].duck and not override:
                    self.pause = True
                    self.guild.duck_manager.duck(self)
                    return
                # self.source = FFmpegPCMAudio(self.queue[0].file)
                self.source = AsyncFFmpegAudio(self.queue[0].file)
                # self.source = AsyncFFmpegPCMWrapper(self.queue[0].file)
                await self.source.start()
                await self.guild.manager.play_start_callback(self.queue[0])
                self.file_volume = self.queue[0].volume
                if next_event:
                    self.next_event = next_event
        else:
            self.stop()
        await self.guild._update_play()

    async def next(self):
        if self.next_event:
            self.next_event.set()
            self.next_event = None
        await self.guild.manager.play_end_callback(self.queue[0])
        self.queue.pop(0)
        self.pause = False
        if self.source:
            self.source.close()
            self.source = None
        await self.play()

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

    async def read(self) -> typing.Optional[bytes]:
        if self.source and not self.pause:
            data = await self.source.read()
            if data:
                arr = np.frombuffer(data, dtype=AUDIO_DATA_TYPE)
                # print("before", arr)
                # arr = np.multiply(arr, .5, dtype=self.guild.dt, casting="unsafe")
                if self.file_volume != 1:
                    arr = arr * self.file_volume

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
        return None

    async def remove(self, audio_file: AudioFile):
        if self.queue[0] == audio_file:
            await self.next()
        else:
            self.queue.remove(audio_file)


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
            self.channel.automation_complete()
        return arr


def setup(bot):
    bot.add_cog(SoundManagerCog(bot))
