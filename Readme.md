# Beatrice

This is Beatrice, a custom Discord bot written for my Discord server. She's named after the character Beatrice from 
Re:Zero and some of her responses are written in-character. Just as Re:Zero Beatrice guards the forbidden library, this 
Beatrice guards my server (or something lol).

Beatrice has a number of notable technologies that were developed along with her, including:

- [nextcord-ormar](https://github.com/pmdevita/nextcord-ormar), easy and quick Django-like database integration 
for Nextcord. Most apps under Beatrice had their database code written in minutes or less with this tool. Database 
management is also streamlined through the use of nxalembic, nextcord-ormar's wrapper around the Alembic migration tool.

- ![Efficient async timers](beatrice/util/timer.py) for apps to schedule events with optional repeats, using native 
DateTime and TimeDelta objects.

- ![Advanced audio playback](beatrice/sound_manager/cog.py) supporting multiple audio channels in a single voice 
channel connection and supporting multiple simultaneous connections across multiple guilds, all mixed 
and processed in realtime, with multithreaded encoding/decoding and async sockets.

- Beatrice Chat, a neural network fine-tuned from Microsoft's DialoGPT to talk like Beatrice.

- Cog Loader, a system for loading cogs as defined by a config file. Cog Loader also allows you to restrict a cog to 
only running in specific guilds or in DMs.

The full set of apps running under Beatrice include:

- Beatrice Chat
- SplatGear, a service to alert you when gear you want is available on Splatoon 2's SplatNet app
- Schedule, a service to schedule Beatrice to alert you at a specific time
- Nicknames, a service to save and load a server's nicknames and apply mass changes to them, such as randomly 
shuffling everyone's usernames or anagraming them. Used for creating chaos.
- A terminal console for editing or viewing info for apps and easing on-the-fly debugging
- A hi command, ping command, and some server specific clean up tasks.
- Basic support for YouTube audio playback and some funny sound effects
- Sound Manager, a service for other cogs that provides support for advanced and efficient audio playback
- Sleep, a service to yell at those still in VC late at night that they should go to sleep
- Random Sound, a service to play random sound effects ala [1 hour of silence occasionally broken up by Vine boom sound effect](https://www.youtube.com/watch?v=ameTtKHP5SA)
- NameColor, a service that allows users to set their username color in a server
- MediaToCDN, a service to rewrite media.discordapp.net links to cdn.discordapp.com links for mobile users
- Typing Mute, a service to mute users who are currently typing with their absurdly loud keyboards

## Configuration

Beatrice requires two different configurations, the main config and the cog config.

### Main config

```ini
[general]
prefix = "-b "
token = discord_bot_token
cogs = cogs.conf
logging_folder =
logging_name = discordbot
db_url = sqlite://db.sqlite3
locale = America/New_York
operator = 1234_id_of_operator_user
user_agent = Beatrice/pmdevita

[clean_up]
users = username:discriminator,username:discriminator

[chat]
socket_path = /tmp/beatrice_chat.sock

[starred]
threshold = 3
emoji = ⭐
```

### Cog config

Cogs can be imported and enabled in three categories

- `[all guilds]` For cogs that are enabled in all guilds
- `[dm]` For cogs that are enabled in all dms
- `[guild_id]` To enable a cog specifically in that guild

```ini
[all guilds]
Beatrice.manage.basic
Beatrice.manage.console
Beatrice.manage.schedule
Beatrice.splatgear

[dm]
Beatrice.manage.basic
Beatrice.manage.schedule
Beatrice.splatgear

[guild_id]
Beatrice.manage.clean_up
Beatrice.chat
Beatrice.sound_manager
Beatrice.youtube
```

## Notes

With the addition of uvloop, a Python 3.9 bug was uncovered that causes the Sound Manager to pin a CPU core to 
100% as soon as any audio is played. If you are using Python 3.9, it's recommended to either disable uvloop or 
move to Python 3.10+.
