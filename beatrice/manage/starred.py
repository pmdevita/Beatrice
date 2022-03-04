import nextcord
import nextcord.ext.commands as commands
from tortoise.models import Model
from tortoise import fields


class StarredMessages:
    message_id = fields.BigIntField(pk=True)
    highlight_id = fields.BigIntField()


class Starred:
    def __init__(self, bot):
        self.bot = bot
        self.threshold = bot.config["starred"]["threshold"]
        self.emoji = bot.config["starred"]["emoji"]


    @commands.Cog.listener("on_raw_reaction_add")
    def on_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        payload.


def setup(bot):
    bot.add_cog(Starred(bot), models=".")

