import discord

from botya import DEBUG
from .owner import Owner


async def setup(bot) -> None:

    await bot.add_cog(
        Owner(bot),
        guilds=[
            discord.Object(id=790337229532299320),
            discord.Object(id=815649625104711720),
            discord.Object(id=1040352846182359122),
        ],
    )
    # await bot.add_cog(Owner(bot))
