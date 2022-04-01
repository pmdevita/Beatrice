from pathlib import Path
from dataclasses import dataclass, field

from nextcord import Message, DMChannel
from nextcord.ext.commands import Bot, Context, Cog
from nextcord.ext.commands.bot import BotBase


@dataclass
class CogPermissions:
    loader: 'CogLoader'
    module_path: str
    direct_messages: bool = False
    all_guilds: bool = False
    guilds: set = field(default_factory=set)


# Layer between the Bot and Cog to handle permissions for the Cog
class BotFilter:
    def __init__(self, bot: Bot, perms: CogPermissions):
        self.__bot = bot
        self.__perms = perms
        self.__cog = None

    # We need to make sure the BotFilter instance, not the Bot, is passed to the cog for its init
    # So we monkeypatch these two functions in and ensure they use this BotFilter as self

    def load_extension(self, *args, **kwargs):
        BotBase.__dict__["load_extension"](self, *args, **kwargs)

    def _load_from_module_spec(self, *args, **kwargs):
        BotBase.__dict__["_load_from_module_spec"](self, *args, **kwargs)

    @classmethod
    def __instancecheck__(cls, instance):   # lmao, Python is wild
        return isinstance(instance, Bot)

    def __getattr__(self, item):
        return getattr(self.__bot, item)

    @property
    def guilds(self):
        return [g for g in self.__bot.guilds if g.id in self.__perms.guilds or self.__perms.all_guilds]

    def add_cog(self, cog: Cog, *args, **kwargs) -> None:
        self.__perms.loader.cog_map[cog] = self.__perms
        self.__cog = cog
        cog._real_inject = cog._inject
        cog._inject = self._inject_bot
        return self.__bot.add_cog(cog, *args, **kwargs)

    # Intercept inject calls to pass the BotFilter instance instead of the Bot
    def _inject_bot(self, bot: BotBase):
        return self.__cog._real_inject(self)

    # Wrap all event listeners with a permissions filter event
    def add_listener(self, func, name):
        return self.__bot.add_listener(self._filter_events(func), name)

    # Filter events based on whether the cog has permission for the guild
    def _filter_events(self, func):
        async def wrapper(*args):
            if len(args):
                try:
                    guild_id = args[0].guild.id
                except AttributeError as e:
                    print("Failed to filter event", args)
                    return await func(*args)
                if guild_id in self.__perms.guilds or self.__perms.all_guilds:
                    return await func(*args)
            else:
                return await func(*args)
        return wrapper


class CogLoader:
    def __init__(self, bot: Bot, file_path):
        self.bot = bot
        if isinstance(file_path, str):
            file_path = Path(file_path)
        self.file_path = file_path
        self.cogs = {}
        self.cog_map = {}
        section = None
        dm_flag = False
        guild_flag = False
        special_flag = False
        with open(self.file_path) as f:
            for l in f.readlines():
                line = l.strip().split("#")[0].strip()
                if line == "":
                    continue
                if line[0] == "[" and line[-1] == "]":
                    section = line[1:-1].lower()
                    dm_flag = section == "dm"
                    guild_flag = section == "all guilds"
                    special_flag = dm_flag or guild_flag
                    if not special_flag:
                        section = int(section)
                elif section is None:
                    raise Exception("Line", l, "not under a section.")
                else:
                    if line in self.cogs:
                        cog = self.cogs[line]
                        cog.all_guilds = guild_flag or cog.all_guilds
                        cog.direct_messages = dm_flag or cog.direct_messages
                    else:
                        cog = CogPermissions(self, module_path=line, direct_messages=dm_flag, all_guilds=guild_flag)
                        self.cogs[line] = cog
                    if not special_flag:
                        cog.guilds.add(section)

    def init_bot(self):
        for key in self.cogs:
            filter = BotFilter(self.bot, self.cogs[key])
            filter.load_extension(key)

    async def process_commands(self, message: Message) -> None:
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.cog:
            perms = self.cog_map[ctx.cog]
            if ctx.guild is not None:
                if ctx.guild.id in perms.guilds or perms.all_guilds:
                    await self.bot.invoke(ctx)
            elif isinstance(ctx.channel, DMChannel):
                if perms.direct_messages:
                    await self.bot.invoke(ctx)
        else:
            await self.bot.invoke(ctx)
