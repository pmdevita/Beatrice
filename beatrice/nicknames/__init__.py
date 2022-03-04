import nextcord.ext.commands as commands
import nextcord.errors as nx_errors
import importlib
from .. import util
from .models import NicknameGroup, Nickname

transformer_map = {
    "pokemon": ".transformers.unscramblers.Pokemon"
}


class Nicknames(commands.Cog):
    def __init__(self, discord):
        self.discord = discord

    @commands.group("nicknames", alias=["nn"])
    async def nickname_group(self, *args):
        pass

    @nickname_group.command("save")
    @commands.has_permissions(manage_nicknames=True)
    async def save_command(self, ctx: commands.Context, *args):
        if len(args) < 1:
            await ctx.send("Error: Name not given for nickname group")
            return
        new_group = await NicknameGroup.create(group_name=args[0])

        async with ctx.typing():
            async for member in ctx.guild.fetch_members():
                if member.nick:
                    new_nick = await Nickname.create(group=new_group, user_id=member.id, nickname=member.nick)

        await ctx.send(f"Saved current nicknames as \"{args[0]}\".")

    @nickname_group.command("load")
    @commands.has_permissions(manage_nicknames=True)
    async def load_command(self, ctx: commands.Context, *args):
        if len(args) < 1:
            await ctx.send("Error: Name not given for nickname group")
            return
        nick_group = await NicknameGroup.get(group_name=args[0])

        override = True
        clear = False

        for i in args[1:]:
            if i == "no override":
                override = False
            if i == "clear":
                clear = True

        async with ctx.typing():
            async for member in ctx.guild.fetch_members():
                nick = await Nickname.filter(group=nick_group, user_id=member.id)
                try:
                    if nick:
                        if member.nick is None or override:
                            await member.edit(nick=nick[0].nickname)
                    else:
                        if clear:
                            await member.edit(nick=None, timeout=None)
                except nx_errors.Forbidden:
                    await member.send(f"Change your nickname to `{nick[0].nickname}`.")
                    print(f"Forbidden: Cannot change name of {member} so messaging instead.")

        await ctx.send(f"Loaded \"{args[0]}\" nicknames.")

    @nickname_group.command("clear")
    @commands.has_permissions(manage_nicknames=True)
    async def clear_command(self, ctx: commands.Context, *args):
        async with ctx.typing():
            async for member in ctx.guild.fetch_members():
                try:
                    if member.nick is not None:
                        await member.edit(nick=None)
                        # pass
                except nx_errors.Forbidden:
                    await member.send(f"Clear your nickname.")
                    print(f"Forbidden: Cannot change name of {member} so messaging instead.")

        await ctx.send(f"Cleared server nicknames.")

    @nickname_group.command("rename")
    @commands.has_permissions(manage_nicknames=True)
    async def rename_command(self, ctx: commands.Context, *args):
        if len(args) < 1:
            await ctx.send("Error: Transformer name not given")
            return
        if args[0] not in transformer_map:
            await ctx.send(f"Error: Unknown transformer \"{args[0]}\"")
            return

        # Dynamically import the transformer
        transformer_path = transformer_map[args[0]]
        p, m = transformer_path.rsplit('.', 1)
        module = importlib.import_module(p, self.__module__)
        transfomer_class = getattr(module, m)

        with ctx.typing():
            transformer = transfomer_class(self)
            await transformer.async_init()

            user_objs = await util.get_recent_users(ctx.guild)
            users = []
            for user in user_objs:
                users.append((user.name, user.id))

            nicks = await transformer.transform_names(users)

            for nick in nicks:
                member = ctx.guild.get_member(nick[1])
                try:
                    await member.edit(nick=nick[0])
                except nx_errors.Forbidden:
                    await member.send(f"Change your nickname to `{nick[0]}`.")
                    print(f"Forbidden: Cannot change name of {member} so messaging instead.")

        await ctx.send("Rename complete.")


def setup(bot):
    bot.add_cog(Nicknames(bot), models=".models")
