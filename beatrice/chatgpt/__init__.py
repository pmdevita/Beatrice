from .cog import Groq as AICog


def setup(bot):
    bot.add_cog(AICog(bot))
