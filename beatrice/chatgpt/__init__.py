from .cog import ChatGPT


def setup(bot):
    bot.add_cog(ChatGPT(bot))
