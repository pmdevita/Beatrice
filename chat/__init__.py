import json
import nextcord
from nextcord.ext import commands
from tortoise.models import Model
from tortoise import fields
import asyncio


class ChatThreads(Model):
    thread_id = fields.BigIntField(pk=True)
    history = fields.TextField()

    class Meta:
        table = "chat_threads"


class ChatBot(commands.Cog):
    def __init__(self, discord):
        self.discord = discord
        self.threads = set()
        self.histories = {}

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        stuff = await ChatThreads.all().values("thread_id", "history")
        for i in stuff:
            self.threads.add(i["thread_id"])
            self.histories[i["thread_id"]] = json.loads(i["history"])

    @commands.command("chat")
    async def start_chat(self, ctx: commands.Context, *args):
        thread = await ctx.message.create_thread(name="Chat")
        thread_row = await ChatThreads.create(thread_id=thread.id, history="[]")
        self.threads.add(thread.id)
        self.histories[thread.id] = []

    @commands.Cog.listener("on_message")
    async def on_message(self, message: nextcord.Message, *arg):
        if message.channel.id not in self.threads:
            return
        me = message.guild.get_member(self.discord.user.id)
        if message.author == me:
            return

        command = {
            "command": "generate",
            "input": message.content,
            "conversation": self.histories[message.channel.id]
        }

        reader, writer = await asyncio.open_unix_connection(self.discord.config["chat"]["socket_path"])
        writer.write(json.dumps(command).encode("utf-8"))
        await writer.drain()
        writer.write_eof()

        response = await reader.read()
        res = json.loads(response.decode("utf-8"))

        self.histories[message.channel.id] = res[1]

        writer.close()
        await writer.wait_closed()

        await message.channel.send(res[0])


def setup(bot):
    bot.add_cog(ChatBot(bot), models=".")
