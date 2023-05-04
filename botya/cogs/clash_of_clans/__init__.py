import discord

from botya import DEBUG
from .clash_of_clans import Clash


async def setup(bot) -> None:

    if DEBUG:
        await bot.add_cog(Clash(bot), guilds=[discord.Object(id=790337229532299320)])
    else:
        await bot.add_cog(Clash(bot))
