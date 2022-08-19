import nextcord
from random import randrange, choice
from datetime import datetime, timedelta
from nextcord.ext import commands
from dataclasses import dataclass

from beatrice.sound_manager import SoundManager, AudioFile
from beatrice.util.timer import TimerTask
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from beatrice.main import DiscordBot

SOUND_BANK = {
    "speen": "assets/speen.opus",
    "mouthful": "assets/mouthful_mode.opus",
    "inhale": "assets/inhale_a_car.opus"
}

MAX_TIME = 60 * 15


@dataclass()
class GuildRandomSound:
    cog: "RandomSound"
    guild: nextcord.Guild
    channel: nextcord.VoiceChannel
    sound_name: str | list
    next_sound: TimerTask = None
    end_playback: TimerTask = None

    async def play_sound(self):
        if isinstance(self.sound_name, list):
            sound_name = choice(self.sound_name)
        else:
            sound_name = self.sound_name

        if isinstance(SOUND_BANK[sound_name], list):
            file = choice(SOUND_BANK[sound_name])
        else:
            file = SOUND_BANK[sound_name]

        await self.cog.sound_manager.queue(self.channel, "notifications", AudioFile(file, volume=1.5))
        self.next_sound = self.cog.bot.timer.schedule_task(datetime.now() + timedelta(seconds=randrange(0, MAX_TIME)),
                                                           self.play_sound)

    async def stop(self):
        self.next_sound.cancel()
        del self.cog.current_playback[self.guild]


class RandomSound(commands.Cog):
    def __init__(self, bot: "DiscordBot"):
        self.bot = bot
        self.current_playback = {}

    async def __async_init__(self):
        self.sound_manager: SoundManager = self.bot.cogs.get("SoundManager")

    @commands.group("randomsound", aliases=["rs"])
    async def random_sound_group(self, *args):
        pass

    @random_sound_group.command("start")
    async def start_playing(self, ctx: commands.Context, *args):
        if len(args) == 0:
            await ctx.send("No sound name given.")
            return

        if ctx.author.voice is None:
            await ctx.send("You aren't currently in a voice channel.")
            return

        for sound_name in args:
            if sound_name not in SOUND_BANK:
                await ctx.send(f"Unknown sound effect {sound_name}.")
                return

        if ctx.guild in self.current_playback:
            await ctx.send("Already playing random sound effects.")
            return

        if len(args) == 1:
            sound_name = args[0]
        else:
            sound_name = args

        channel = ctx.author.voice.channel

        now = datetime.now()
        end = now + timedelta(hours=1)

        grs = GuildRandomSound(self, ctx.guild, channel, sound_name)

        next_sound = self.bot.timer.schedule_task(now + timedelta(seconds=randrange(0, MAX_TIME)), grs.play_sound)
        end_playback = self.bot.timer.schedule_task(end, grs.stop)

        grs.next_sound = next_sound
        grs.end_playback = end_playback

        self.current_playback[ctx.guild] = grs

        await ctx.send(f"Starting one hour of random {sound_name} in {channel.name}")

    @random_sound_group.command("stop")
    async def stop_playing(self, ctx: commands.Context, *args):
        if ctx.guild in self.current_playback:
            grs = self.current_playback[ctx.guild]
            await grs.stop()
            await ctx.send("Stopping playback")
        else:
            await ctx.send("Not current playing random sounds.")


def setup(bot: "DiscordBot"):
    bot.add_cog(RandomSound(bot))
