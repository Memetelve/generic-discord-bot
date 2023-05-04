import discord

from .test import Test


async def setup(bot) -> None:

    await bot.add_cog(Test(bot), guilds=[discord.Object(id=790337229532299320)])
