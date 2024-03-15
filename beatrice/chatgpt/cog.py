import nextcord
import openai
from groq import AsyncGroq
from anthropic import AsyncAnthropic
import tiktoken
from beatrice.util.slash_compat import Cog
from nextcord.ext import commands
from typing import TYPE_CHECKING

from .prompts import prompt

if TYPE_CHECKING:
    from beatrice.main import DiscordBot


class AIChat(Cog):
    def __init__(self, bot: "DiscordBot"):
        self.bot = bot
        self.token_budget: int = int(bot.config["chat_gpt"].get("token_budget", 700))

    async def __async_init__(self):
        pass

    async def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    async def inference(self, messages: list[dict]) -> str:
        raise NotImplementedError

    @commands.Cog.listener("on_message")
    async def on_message(self, message: nextcord.Message, *args):
        guild = message.guild
        reference = message.reference
        is_reply = False
        if reference:
            reference_guild = self.bot.get_guild(reference.guild_id)
            reference_channel = reference_guild.get_channel(reference.channel_id)
            reference_message = await reference_channel.fetch_message(reference.message_id)
            is_reply = reference_message.author == guild.me
        if (guild.me in message.mentions and message.author != guild.me) or is_reply:
            await self.reply_to(message)

    async def reply_to(self, message: nextcord.Message):
        async with message.channel.typing():
            budget = self.token_budget
            budget -= await self.count_tokens(prompt)
            log = []
            raw_messages = [message]
            async for before_message in message.channel.history(limit=10, before=message):
                raw_messages.append(before_message)
            for message in raw_messages:
                if budget < 0:
                    break
                if message.author == self.bot.user:
                    entry = {
                        "role": "assistant",
                        "content": message.content
                    }
                else:
                    entry = {
                        "role": "user",
                        "content": f"{message.author.name}: {await self.sanitize_message(message)}"
                    }
                budget -= await self.count_tokens(entry["content"])
                log.insert(0, entry)

            log.insert(0, {"role": "system", "content": prompt})
            result = await self.inference(log)
            result = self.remove_character_prefix(result)
            await message.channel.send(result)

    def remove_character_prefix(self, text):
        lines = []
        for line in text.split("\n"):
            if line.startswith("Beatrice:"):
                lines.append(line[len("Beatrice:"):].lstrip())
            else:
                lines.append(line)
        return "\n".join(lines)

    async def sanitize_message(self, message: nextcord.Message):
        text = message.content
        for mention in message.mentions:
            text = text.replace(f"<@{mention.id}>", mention.name)
        return text


class ChatGPT(AIChat):
    def __init__(self, bot: "DiscordBot"):
        super().__init__(bot)
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        openai.api_key = bot.config["chat_gpt"]["key"]

    def __async_init__(self):
        openai.aiosession.set(self.bot.session)

    async def count_tokens(self, text: str) -> int:
        return len(self.enc.encode(text))

    async def inference(self, messages: list[dict]) -> str:
        completion = await openai.ChatCompletion.acreate(model="gpt-3.5-turbo", messages=messages)
        result = completion.choices[0].message.content
        return result


class Groq(AIChat):
    def __init__(self, bot: "DiscordBot"):
        super().__init__(bot)
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.client = AsyncGroq(api_key=bot.config["groq"]["key"])
        self.model = bot.config["groq"]["model"]
        self.token_budget = int(bot.config["groq"]["token_budget"])

    async def count_tokens(self, text: str) -> int:
        return len(self.enc.encode(text))

    async def inference(self, messages: list[dict]) -> str:
        message = await self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=300)
        return message.choices[0].message.content


class Anthropic(AIChat):
    def __init__(self, bot: "DiscordBot"):
        super().__init__(bot)
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.anthropic = AsyncAnthropic(api_key=bot.config["anthropic"]["key"])
        self.model = "claude-3-haiku-20240307"
        self.token_budget = int(bot.config["anthropic"]["token_budget"])

    async def count_tokens(self, text: str) -> int:
        # Does not give an accurate result for newer models, you have to
        # get a response from the API for that :/
        return await self.anthropic.count_tokens(text)

    async def inference(self, messages: list[dict]) -> str:
        # Anthropic is a stick in the mud
        system_message = "\n".join([m["content"] for m in messages if m["role"] == "system"])
        fixed_messages = []
        for m in messages:
            if m["role"] == "system":
                continue
            if not fixed_messages:
                fixed_messages.append(m)
                continue
            if m["role"] == fixed_messages[-1]["role"]:
                fixed_messages[-1]["content"] += "\n" + m["content"]
            else:
                fixed_messages.append(m)

        # How annoying can you be?
        if not fixed_messages:
            print(fixed_messages)
            raise Exception("No messages?")

        if fixed_messages[0]["role"] == "assistant":
            fixed_messages.insert(0, {"role": "user", "content": "..."})

        message = await self.anthropic.messages.create(model=self.model, messages=fixed_messages,
                                                       max_tokens=300, system=system_message)
        return message.content[0].text
