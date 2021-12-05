import nextcord_tortoise
from nextcord.ext import commands
from tortoise.models import Model
from tortoise import fields
from tortoise.queryset import Q
from util import send_list
from datetime import datetime, timedelta
from random import randrange
import json


class GearRequests(Model):
    id = fields.IntField(pk=True)
    user = fields.BigIntField()
    gear_type = fields.IntField(null=True)
    gear_id = fields.IntField(null=True)
    brand_id = fields.IntField(null=True)
    skill_id = fields.IntField(null=True)
    last_messaged = fields.DatetimeField()

    class Meta:
        table = "splatgear_requests"


class GearType:
    HEAD = 0
    CLOTHES = 1
    SHOES = 2


class SplatGear(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.head_gear = {}
        self.clothes_gear = {}
        self.shoes_gear = {}
        self.brands = {}
        self.skills = {}

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        async with self.discord.session.get("https://splatoon2.ink/data/locale/en.json") as response:
            data = await response.json()
            for gear in data["gear"]:
                # Use gear sub categories instead of unordered
                if "name" not in data["gear"][gear]:
                    for sub_gear in data["gear"][gear]:
                        gear_name = data["gear"][gear][sub_gear]["name"]
                        if gear == "clothes":
                            self.clothes_gear[gear_name] = sub_gear
                        elif gear == "shoes":
                            self.shoes_gear[gear_name] = sub_gear
                        elif gear == "head":
                            self.head_gear[gear_name] = sub_gear
            for brand in data["brands"]:
                self.brands[data["brands"][brand]["name"]] = brand
            for skill in data["skills"]:
                self.skills[data["skills"][skill]["name"]] = skill

        self.timer = self.discord.timer.schedule_task(datetime.now() + timedelta(minutes=randrange(5, 55)), self.check_gear, timedelta(hours=2))

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
        brand_name = None
        gear = None
        gear_name = None
        skill = None
        skill_name = None
        kwargs = {"user": ctx.author.id, "last_messaged": datetime.now(self.discord.timer.timezone) - timedelta(days=2)}
        for i in args:
            if i in self.brands:
                brand = self.brands[i]
                brand_name = i
                kwargs["brand_id"] = brand
            elif i in self.head_gear:
                gear = self.head_gear[i]
                gear_name = i
                kwargs["gear_type"] = GearType.HEAD
                kwargs["gear_id"] = gear
            elif i in self.clothes_gear:
                gear = self.clothes_gear[i]
                gear_name = i
                kwargs["gear_type"] = GearType.CLOTHES
                kwargs["gear_id"] = gear
            elif i in self.shoes_gear:
                gear = self.shoes_gear[i]
                gear_name = i
                kwargs["gear_type"] = GearType.SHOES
                kwargs["gear_id"] = gear
            elif i in self.skills:
                skill = self.skills[i]
                skill_name = i
                kwargs["skill_id"] = skill
            else:
                await ctx.send(f"Unknown property \"{i}\"")
                return
        gear_row = await GearRequests.create(**kwargs)
        message = f"Added alert for gear with {self.format_gear_request(gear_name, brand_name, skill_name)}."
        await ctx.send(message)

    def format_gear_request(self, gear, brand, skill):
        message = ""
        if gear:
            message += f" type {gear}"
        if brand:
            if gear:
                message += ","
            message += f" brand {brand}"
        if skill:
            if brand and gear:
                message += ", and"
            elif brand or gear:
                message += " and"
            message += f" skill {skill}"
        if message[0] == " ":
            message = message[1:]
        return message

    @splatgear_group.command("list")
    async def list_properties(self, ctx: commands.Context, *args):
        if len(args) == 0:
            await ctx.send("Error: please request lists of either gear and type, skill, or brand.")
            return
        request_type = args[0].lower()
        prop_dict = None
        if request_type == "brand" or request_type == "brands":
            prop_dict = self.brands
        elif request_type == "gear" or request_type == "gears":
            gear_type = None
            if len(args) >= 2:
                gear_type = args[1].lower()
            if gear_type == "clothes":
                prop_dict = self.clothes_gear
            elif gear_type == "shoes" or gear_type == "shoe":
                prop_dict = self.shoes_gear
            elif gear_type == "head" or gear_type == "hat" or gear_type == "hats":
                prop_dict = self.head_gear
            else:
                await ctx.send("Error: Unknown gear subtype (must be head, clothes, or shoes)")
                return
        elif request_type == "skill" or request_type == "skills":
            prop_dict = self.skills
        else:
            await ctx.send(f"Error: Unknown type {args[0]}")
            return

        await send_list(ctx.send, prop_dict.keys())

    @splatgear_group.command("check")
    async def check_command(self, ctx: commands.Context, *args):
        await self.check_gear()

    async def check_gear(self, *args):
        async with self.discord.session.get("https://splatoon2.ink/data/merchandises.json") as response:
            data = await response.json()
        for merch in data["merchandises"]:
            gear_type = merch["gear"]["kind"]
            if gear_type == "head":
                gear_type = GearType.HEAD
            elif gear_type == "clothes":
                gear_type = GearType.CLOTHES
            else:
                gear_type = GearType.SHOES
            gear_name = merch["gear"]["name"]
            brand_name = merch["gear"]["brand"]["name"]
            skill_name = merch["skill"]["name"]

            gear_id = int(merch["gear"]["id"])
            brand_id = int(merch["gear"]["brand"]["id"])
            skill_id = int(merch["skill"]["id"])

            rows = await GearRequests.filter(
                Q(Q(gear_id=gear_id) | Q(gear_id=None)) &
                Q(Q(gear_type=gear_type) | Q(gear_type=None)) &
                Q(Q(brand_id=brand_id) | Q(brand_id=None)) &
                Q(Q(skill_id=skill_id) | Q(skill_id=None)) &
                Q(last_messaged__lte=datetime.now(self.discord.timer.timezone) - timedelta(1))
            )
            for request in rows:
                user = self.discord.get_user(request.user)
                channel = await self.discord.create_dm(user)
                message = f"SplatGear Alert! An item with {self.format_gear_request(gear_name, brand_name, skill_name)} " \
                          f"is available on the SplatNet store! (Your request was for an item with " \
                          f"{self.format_gear_request(gear_name if request.gear_id else None, brand_name if request.brand_id else None, skill_name if request.skill_id else None)})"
                await channel.send(message)
                request.last_messaged = datetime.now(self.discord.timer.timezone)
                await request.save()

    @splatgear_group.command("watches", aliases=["requests"])
    async def watches(self, ctx: commands.Context, *args):
        user = ctx.author.id
        message = "```\n"
        async for watch in GearRequests.filter(user=user):
            message += self.format_gear_request(watch.gear_id, watch.brand_id, watch.skill_id)


def setup(bot):
    bot.add_cog(SplatGear(bot), models=".")
