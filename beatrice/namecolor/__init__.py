import nextcord
import ormar
from nextcord_ormar import AppModel, OrmarApp
from nextcord.ext import commands

MetaModel = OrmarApp.create_app("namecolor")


class NameColorRoles(AppModel):
    class Meta(MetaModel):
        pass
    user_id: int = ormar.BigInteger(primary_key=True)
    role: int = ormar.BigInteger()
    color: str = ormar.String(max_length=6)


class NameColor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def hex_to_rgb(self, hex_string):
        return int(hex_string[:2], 16), int(hex_string[2:4], 16), int(hex_string[4:], 16)

    @commands.group("namecolor", aliases=["nc"])
    async def namecolor_group(self, *args):
        if args[0].invoked_subcommand is not None:
            return None
        if args[0].subcommand_passed is not None:
            return await self.color_change(args[0], args[0].subcommand_passed)
        return None

    @namecolor_group.command("change")
    async def color_change(self, ctx: commands.Context, *args):
        db_color = await NameColorRoles.objects.get_or_none(user_id=ctx.author.id)
        color_hex = args[0]
        if color_hex.startswith("#"):
            color_hex = color_hex[1:]
        color = nextcord.Color.from_rgb(*self.hex_to_rgb(color_hex))
        if db_color:
            role = ctx.guild.get_role(db_color.role)
            await role.edit(color=color)
            db_color.color = color_hex
            await db_color.update()
            await ctx.send("Changed color role!")
        else:
            role = await ctx.guild.create_role(name=f"{ctx.author.name} Color",
                                               color=color,
                                               reason="Beatrice NameColor change")
            await NameColorRoles.objects.create(user_id=ctx.author.id, role=role.id, color=color_hex)
            await ctx.author.add_roles(role)
            await ctx.send("Added color role!")

    @namecolor_group.command("delete")
    async def color_delete(self, ctx: commands.Context, *args):
        db_color = await NameColorRoles.objects.get_or_none(user_id=ctx.author.id)
        role = ctx.guild.get_role(db_color.role)
        await role.delete(reason="Beatrice NameColor delete")
        await db_color.delete()
        await ctx.send("Deleted color role!")





def setup(bot):
    bot.add_cog(NameColor(bot))


