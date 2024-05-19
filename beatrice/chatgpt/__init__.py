from .cog import Anthropic as AICog


def setup(bot):
    bot.add_cog(AICog(bot))
