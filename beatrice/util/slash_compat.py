import nextcord
from nextcord.ext import commands
from nextcord.ext.commands.core import unwrap_function, get_signature_parameters


class _ComboCommand:
    def __init__(self, app_cmd: nextcord.SlashApplicationCommand, msg_cmd: commands.Command):
        self.app_cmd = app_cmd
        self.msg_cmd = msg_cmd


class _CogMetaParent:
    def __new__(cls, *args, **kwargs):
        new_cls = super().__new__(cls, *args, **kwargs)
        new_methods = {}
        for key, value in new_cls.__dict__.items():
            if isinstance(value, _ComboCommand):
                new_methods[key + "_msgcmd"] = value.msg_cmd
                setattr(new_cls, key, value.app_cmd)
        for key, value in new_methods.items():
            setattr(new_cls, key, value)
        return new_cls


# We define a subclass of CogMeta so that we can monkey patch its class lineage
class CogMeta(commands.CogMeta):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


CogMeta.__bases__ = CogMeta.__bases__ + (_CogMetaParent, type)


class Cog(commands.Cog, metaclass=CogMeta):
    pass


class Command(commands.Command):
    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, function: '_CogCommSlashWrapper') -> None:
        self._callback = function
        real_function = getattr(function, "func", function)
        unwrap = unwrap_function(real_function)
        self.module = unwrap.__module__

        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}

        self.params = get_signature_parameters(real_function, globalns)


# Wraps a Cog Command to convert its Context to an Interaction
def _command_context_to_interaction(func):
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        return await func(self, CommandInteraction(ctx), *args, **kwargs)

    return wrapper


def command(name, aliases=None, **kwargs):
    """A command.Command-like decorator that works alongside a slash command decorator"""
    def wrapper(func):
        wrapped_comm = _command_context_to_interaction(func.callback)
        wrapped_comm.func = func.callback
        comm = Command(wrapped_comm, name=name, aliases=aliases if aliases else [], **kwargs)
        return _ComboCommand(func, comm)

    return wrapper


class CommandInteraction:
    """Wrap a commands.Context object to provide compatibility for slash commands"""

    def __init__(self, ctx: commands.Context):
        self._ctx = ctx

    def __getattr__(self, item):
        return getattr(self._ctx, item)

    @property
    def user(self):
        return self._ctx.author

    @property
    def channel_id(self):
        return self._ctx.channel.id
