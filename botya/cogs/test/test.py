import discord
from discord.ext import commands


class Test(commands.Cog, name="Testing", description=""):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hidden = True

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx, id):
        message = await ctx.channel.fetch_message(int(id))

        print(message.components)

    @commands.command()
    @commands.is_owner()
    async def check_help(self, ctx):
        """
        iterate through all tree.commands and check if they have a description, all arguments have a description
        iterate through all cogs and check if they have a description
        iterate through all groups and check if they have a description

        send embed with results (✅/🟥)
        """

        embed = discord.Embed(title="Check Help", color=discord.Color.blue())

        cogs = []
        groups = []
        commands = []

        for cog_str in self.bot.cogs:

            cog = self.bot.cogs[cog_str]

            emoji = "✅"
            if getattr(cog, "hidden", False):
                continue
            if not getattr(cog, "description", None):
                emoji = "🟥"
            cogs.append(f"{emoji}{cog.qualified_name}")

            for com in cog.get_app_commands():
                if isinstance(com, discord.app_commands.commands.Group):
                    for subcom in com.commands:
                        emoji = "✅"
                        if (
                            not getattr(subcom, "description", None)
                            or getattr(subcom, "description", None) == "…"
                        ):
                            emoji = "🟥"
                            break
                        else:
                            for param in subcom.parameters:
                                if (
                                    not getattr(param, "description", None)
                                    or getattr(param, "description", None) == "…"
                                ):
                                    emoji = "🟥"
                                    break
                    groups.append(f"{emoji}{com.name}")
                else:
                    emoji = "✅"
                    if (
                        not getattr(com, "description", None)
                        or getattr(com, "description", None) == "…"
                    ):
                        emoji = "🟥"
                    else:
                        for param in com.parameters:
                            if (
                                not getattr(param, "description", None)
                                or getattr(param, "description", None) == "…"
                            ):
                                emoji = "🟥"

                    commands.append(f"{emoji}{com.name}")

        # add cogs, groups and commands to embed
        embed.add_field(name="Cogs", value="\n".join(cogs), inline=False)
        embed.add_field(name="Groups", value="\n".join(groups), inline=False)
        embed.add_field(name="Commands", value="\n".join(commands), inline=False)

        await ctx.send(embed=embed)
