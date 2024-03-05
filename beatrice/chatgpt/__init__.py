from .cog import Groq


def setup(bot):
    bot.add_cog(Groq(bot))
