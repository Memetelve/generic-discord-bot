import discord

from botya import DEBUG
from .internal import Internal


async def setup(bot) -> None:
    if DEBUG:
        await bot.add_cog(Internal(bot), guilds=[discord.Object(id=790337229532299320)])
    else:
        await bot.add_cog(Internal(bot))
