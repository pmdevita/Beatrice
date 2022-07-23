import nextcord
import typing
from nextcord.ext import commands
from tortoise.models import Model, MODEL
from tortoise import fields, BaseDBAsyncClient
from tortoise.queryset import Q
from beatrice.util import send_list
from datetime import datetime, timedelta
from random import randrange
from enum import Enum


class Brands(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=30)

    class Meta:
        table = "splatgear_brands"


class Skills(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=30)

    class Meta:
        table = "splatgear_skills"


class GearEnum(Enum):
    Head = "head"
    Shoes = "shoes"
    Clothes = "clothes"


class Gear(Model):
    _pid = fields.CharField(max_length=15, pk=True)
    id = fields.IntField()
    type = fields.CharEnumField(GearEnum)
    name = fields.CharField(max_length=30)

    @classmethod
    async def create(
        cls: typing.Type[MODEL], using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Any
    ) -> MODEL:
        kwargs["_pid"] = f"{kwargs['type']}_{kwargs['id']}"
        return await super().create(**kwargs, using_db=using_db)

    class Meta:
        table = "splatgear_gear"


class GearRequests(Model):
    id = fields.IntField(pk=True)
    user = fields.BigIntField()
    gear = fields.ForeignKeyField("SplatGear.Gear", related_name="requests", null=True, on_delete=fields.CASCADE)
    brand = fields.ForeignKeyField("SplatGear.Brands", related_name="requests", null=True, on_delete=fields.CASCADE)
    skill = fields.ForeignKeyField("SplatGear.Skills", related_name="requests", null=True, on_delete=fields.CASCADE)
    last_messaged = fields.DatetimeField()

    class Meta:
        table = "splatgear_requests"


class SplatGear(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.head_gear = {}
        self.clothes_gear = {}
        self.shoes_gear = {}
        self.brands = {}
        self.skills = {}

    async def __async_init__(self):
        await self._synchronize_gear()
        self.timer = self.discord.timer.schedule_task(datetime.now() + timedelta(minutes=randrange(5, 55)), self.check_gear, timedelta(hours=2))

    async def _synchronize_gear(self):
        async with self.discord.session.get("https://splatoon2.ink/data/locale/en.json") as response:
            data = await response.json()
            for gear_type in GearEnum:
                await self._synchronize_gear_list(data["gear"][gear_type.value], Gear, gear_type=gear_type.value)
            # Synchronize brands
            await self._synchronize_gear_list(data["brands"], Brands)
            # Synchronize skills
            await self._synchronize_gear_list(data["skills"], Skills)

    async def _synchronize_gear_list(self, gear_list, model: Model, gear_type=None):
        gears = {int(gear): gear_list[gear]["name"] for gear in gear_list}
        async for gear_row in model.all():
            # If we are using types, make sure this has a matching one first
            if gear_type:
                if gear_type != gear_row.type.value:
                    continue
            # Remove from our dictionary if there is a match, otherwise delete it
            if gears.get(gear_row.id, None) == gear_row.name:
                gears.pop(gear_row.id)
            else:
                await gear_row.delete()
        kwargs = {}
        if gear_type:
            kwargs["type"] = gear_type
        for gear in gears:
            await model.create(id=gear, name=gears[gear], **kwargs)

    @commands.group("splatgear")
    async def splatgear_group(self, *args):
        pass

    @splatgear_group.command("help")
    async def help(self, ctx: commands.Context, *args):
        await ctx.send("""
        ```
Splatgear can notify you if a specific gear you are looking for is available in SplatNet.
Usage:
    splatgear list (gear|brands|skills) (head|clothes|shoes)
    - List attributes of a specific type. Gear needs head, clothes, or shoes also specified.
    splatgear add "gear" "brand" "skill"
    - List up to three attributes (one in each category) to watch for.
    - Examples:
      - splatgear add "SquidForce" "White Headband" "Ink Saver (Main)"
      - splatgear add "Cold-Blooded"
      - splatgear add "Skate Helmet" "Ink Recovery Up"
    splatgear watches
    - List current gear watches you have set along with the watch id
    splatgear delete (id)
    - Delete a watch by its id
        ```
        """)

    @splatgear_group.command("add")
    async def add(self, ctx: commands.Context, *args):
        brand = None
        gear = None
        skill = None
        kwargs = {"user": ctx.author.id, "last_messaged": datetime.now(self.discord.timer.timezone) - timedelta(days=2)}
        for i in args:
            new_brand = await Brands.get_or_none(name=i)
            if new_brand:
                brand = new_brand
                kwargs["brand"] = brand
            new_gear = await Gear.get_or_none(name=i)
            if new_gear:
                gear = new_gear
                kwargs["gear"] = gear
            new_skill = await Skills.get_or_none(name=i)
            if new_skill:
                skill = new_skill
                kwargs["skill"] = skill
            if new_brand is None and new_gear is None and new_skill is None:
                await ctx.send(f"Unknown property \"{i}\"")
                return
        gear_row = await GearRequests.create(**kwargs)
        await ctx.send(f"Added alert for gear with {self.format_gear_request(gear, brand, skill)}.")

    def format_gear_request(self, gear: typing.Optional[Gear], brand: typing.Optional[Brands], skill: typing.Optional[Skills]):
        message = ""
        if gear:
            message += f" type {gear.name}"
        if brand:
            if gear:
                message += ","
            message += f" brand {brand.name}"
        if skill:
            if brand and gear:
                message += ", and"
            elif brand or gear:
                message += " and"
            message += f" skill {skill.name}"
        if message[0] == " ":
            message = message[1:]
        return message

    @splatgear_group.command("list")
    async def list_properties(self, ctx: commands.Context, *args):
        if len(args) == 0:
            await ctx.send("Error: please request lists of either gear and type, skill, or brand.")
            return
        request_type = args[0].lower()
        if request_type == "brand" or request_type == "brands":
            with ctx.channel.typing():
                kinds = [i.name for i in await Brands.all()]
        elif request_type == "gear" or request_type == "gears":
            given_type = None
            gear_type = None
            if len(args) >= 2:
                given_type = args[1].lower()
            if given_type == "clothes":
                gear_type = GearEnum.Clothes
            elif given_type == "shoes" or gear_type == "shoe":
                gear_type = GearEnum.Shoes
            elif given_type == "head" or gear_type == "hat" or gear_type == "hats":
                gear_type = GearEnum.Head
            else:
                await ctx.send("Error: Unknown gear subtype (must be head, clothes, or shoes)")
                return
            with ctx.channel.typing():
                kinds = [i.name for i in await Gear.filter(type=gear_type)]
        elif request_type == "skill" or request_type == "skills":
            with ctx.channel.typing():
                kinds = [i.name for i in await Skills.all()]
        else:
            await ctx.send(f"Error: Unknown type {args[0]}")
            return
        await send_list(ctx.send, kinds)

    @splatgear_group.command("check")
    async def check_command(self, ctx: commands.Context, *args):
        await self.check_gear()

    async def check_gear(self, *args):
        async with self.discord.session.get("https://splatoon2.ink/data/merchandises.json") as response:
            data = await response.json()
        for merch in data["merchandises"]:
            given_gear_type = merch["gear"]["kind"]
            if given_gear_type == "head":
                gear_type = GearEnum.Head
            elif given_gear_type == "clothes":
                gear_type = GearEnum.Clothes
            else:
                gear_type = GearEnum.Shoes
            gear = await Gear.get(id=int(merch["gear"]["id"]), type=gear_type)
            brand = await Brands.get(id=int(merch["gear"]["brand"]["id"]))
            skill = await Skills.get(id=int(merch["skill"]["id"]))

            rows = await GearRequests.filter(
                Q(Q(gear=gear) | Q(gear_id=None)) &
                Q(Q(brand=brand) | Q(brand_id=None)) &
                Q(Q(skill=skill) | Q(skill_id=None)) &
                Q(last_messaged__lte=datetime.now(self.discord.timer.timezone) - timedelta(hours=12))
            ).select_related("gear", "brand", "skill")

            for request in rows:
                gear_image = self._get_image_link(merch["gear"]["image"])
                skill_image = self._get_image_link(merch["skill"]["image"])
                brand_image = self._get_image_link(merch["gear"]["brand"]["image"])
                # if request.gear is None:
                #     if request.skill:
                #     else:
                #         image_link = self._get_image_link(merch["gear"]["brand"]["image"])
                user = self.discord.get_user(request.user)
                channel = await self.discord.create_dm(user)
                message = f"An item with {self.format_gear_request(gear, brand, skill)} " \
                          f"is available on the SplatNet store! (Your request was for an item with " \
                          f"{self.format_gear_request(request.gear, request.brand, request.skill)})"
                embed1 = nextcord.Embed(title="Splatgear Alert!", description=message)
                embed2 = None

                embed1.set_image(gear_image)
                embed1.set_thumbnail(brand_image)
                embed2 = nextcord.Embed()
                embed2.set_thumbnail(skill_image)
                embeds = [embed1, embed2]

                # Kind of a mess but decides where images should go based on request options
                # thumbnail_priority = []
                # if request.skill:
                #     thumbnail_priority.append(skill_image)
                # if request.brand:
                #     thumbnail_priority.append(brand_image)
                # if request.gear:
                #     embed1.set_image(gear_image)
                #     thumbnail = thumbnail_priority.pop(0)
                #     if thumbnail:
                #         embed1.set_thumbnail(thumbnail)
                #     if thumbnail_priority:
                #         embed2 = nextcord.Embed()
                #         embed2.set_thumbnail(thumbnail_priority[0])
                # else:
                #     thumbnail = thumbnail_priority.pop(0)
                #     if thumbnail:
                #         embed1.set_thumbnail(thumbnail)
                #     if thumbnail_priority:
                #         embed1.set_image(thumbnail_priority[0])
                # embeds = [embed1]
                # if embed2:
                #     embeds.append(embed2)
                await channel.send(embeds=embeds)
                request.last_messaged = datetime.now(self.discord.timer.timezone)
                await request.save()

    def _get_image_link(self, uri):
        return f"https://splatoon2.ink/assets/splatnet{uri}"

    @splatgear_group.command("watches", aliases=["requests"])
    async def watches(self, ctx: commands.Context, *args):
        with ctx.channel.typing():
            user = ctx.author.id
            message = "```\n"
            i = 1
            async for watch in GearRequests.filter(user=user).select_related("gear", "brand", "skill"):
                message += f"{i}: {self.format_gear_request(watch.gear, watch.brand, watch.skill)}\n"
                i += 1
            if i == 1:
                await ctx.send("You currently do not have any watches set.")
            else:
                message += "```"
                await ctx.send(message)

    @splatgear_group.command("delete")
    async def delete(self, ctx: commands.Context, *args):
        ids = []
        for i in args:
            try:
                ids.append(int(i))
            except ValueError:
                await ctx.send(f"Error: {i} is not a number.")
                return
        rows = await GearRequests.filter(user=ctx.author.id, id__in=ids)
        if not rows:
            await ctx.send("Error: No watches found.")
            return
        if len(rows) == 1:
            message = f"Deleted watch {rows[0].id}."
        elif len(rows) == 2:
            message = f"Deleted watches {rows[0].id} and {rows[1].id}."
        else:
            message = "Deleted watches " + ", ".join([str(i.id) for i in rows[:-1]]) + f", and {rows[-1].id}."
        for row in rows:
            await row.delete()
        await ctx.send(message)


def setup(bot):
    bot.add_cog(SplatGear(bot), models=".")
