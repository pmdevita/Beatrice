import nextcord.ext.commands as commands
import aioconsole
import asyncio


def class_register(cls):
    cls._commands = {}
    for methodname in dir(cls):
        method = getattr(cls, methodname)
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
class Console(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.command_task = None
        self.commands = {}
        # self.command = Commands()

    async def __async_init__(self):
        self.command_task = asyncio.create_task(self.get_command())

    async def get_command(self):
        command = await aioconsole.ainput()
        try:
            await self.parse_command(command)
        except Exception as e:
            print("Error parsing command:", e)
        self.command_task = asyncio.create_task(self.get_command())

    async def parse_command(self, command):
        command_tokens = command.split(" ")
        i = 0
        while i < len(command_tokens):
            while command_tokens[i][0] == "\"" and command_tokens[i][-1] != "\"" and i < len(command_tokens) - 1:
                command_tokens[i] = command_tokens[i] + " " + command_tokens[i+1]
                command_tokens.pop(i+1)
            if command_tokens[i][0] == "\"" and command_tokens[i][-1] == "\"":
                command_tokens[i] = command_tokens[i][1: -1]
            i += 1
        func = self._commands.get(command_tokens[0], None)
        if func:
            await func(self, *command_tokens[1:])

    @register("timers", aliases=["t"])
    async def timers(self):
        print(self.discord.timer.tasks)






def setup(bot):
    bot.add_cog(Console(bot))
