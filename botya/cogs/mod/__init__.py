import discord

from botya import DEBUG
from .mod import Mod

async def setup(bot) -> None:

    if DEBUG:
        await bot.add_cog(Mod(bot), guilds = [discord.Object( id = 790337229532299320 )])
    else:
        await bot.add_cog(Mod(bot))