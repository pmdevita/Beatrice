import nextcord.ext.commands as commands
import aioconsole
import asyncio

from beatrice.util.background_tasks import BackgroundTasks


def class_register(cls):
    cls._commands = {}
    for method_name in dir(cls):
        method = getattr(cls, method_name)
        if hasattr(method, '_prop'):
            cls._commands[method._prop["name"]] = method
            if method._prop["aliases"]:
                for alias in method._prop["aliases"]:
                    cls._commands[alias] = method
    return cls


def register(name, aliases=None):
    def wrapper(func):
        func._prop = {"name": name, "aliases": aliases}
        return func

    return wrapper


@class_register
class Console(commands.Cog, BackgroundTasks):
    def __init__(self, discord: commands.Bot):
        super().__init__()
        self.discord = discord
        self.command_task = None
        self.commands = {}
        self._cancel = False
        # self.command = Commands()

    async def __async_init__(self):
        self.command_task = asyncio.create_task(self.get_command())

    async def get_command(self):
        while not self._cancel:
            command = await aioconsole.ainput()
            try:
                self.start_background_task(self.parse_command(command))
            except Exception as e:
                print("Error parsing command:", e)

    async def parse_command(self, command):
        if command == "":
            return
        command_tokens = command.split(" ")
        i = 0
        while i < len(command_tokens):
            while command_tokens[i][0] == "\"" and command_tokens[i][-1] != "\"" and i < len(command_tokens) - 1:
                command_tokens[i] = command_tokens[i] + " " + command_tokens[i + 1]
                command_tokens.pop(i + 1)
            if command_tokens[i][0] == "\"" and command_tokens[i][-1] == "\"":
                command_tokens[i] = command_tokens[i][1: -1]
            i += 1
        func = self._commands.get(command_tokens[0], None)
        if func:
            await func(self, *command_tokens[1:])

    @register("timers", aliases=["t"])
    async def timers(self):
        print(self.discord.timer.tasks)

    @register("guilds")
    async def guilds(self):
        print(self.discord.guilds)

    @register("cogs")
    async def cogs(self):
        print(self.discord.cogs)

    @register("users")
    async def users(self, guild_id):
        guild = self.discord.get_guild(int(guild_id))
        print(guild.members)

    @register("channels")
    async def channels(self, guild_id):
        guild = self.discord.get_guild(int(guild_id))
        print(guild.channels)

    @register("quit")
    async def quit(self):
        self._cancel = True
        self.command_task.cancel()
        asyncio.ensure_future(self.discord.close())
        # await self.discord.close()


def setup(bot):
    bot.add_cog(Console(bot))
