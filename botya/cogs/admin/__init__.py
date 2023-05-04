import discord

from botya import DEBUG
from .admin import Admin

async def setup(bot) -> None:

    if DEBUG:
        await bot.add_cog(Admin(bot), guilds = [discord.Object( id = 790337229532299320 )])
    else:
        await bot.add_cog(Admin(bot))