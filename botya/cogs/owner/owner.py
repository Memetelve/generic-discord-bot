import discord
import os
import asyncio

from discord import app_commands
from discord.ext import commands

from botya.core.utils.checks import is_owner
from botya.core.utils.embed import Embed

from .events import OwnerEvents


class Owner(OwnerEvents, commands.Cog, name="Owner", description=""):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hidden = True

    @app_commands.command(name="reload_cog")
    @is_owner()
    async def _reload_ext(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if os.name == "nt":
            folder_path = r"\botya\cogs"
        else:
            folder_path = r"/botya/cogs"

        full_path = str(os.getcwd()) + folder_path

        cogs = [
            f"botya.cogs.{f}"
            for f in os.listdir(full_path)
            if os.path.isdir(os.path.join(full_path, f))
        ]

        cogs.append("ALL")

        numerical_cog_list = "\n".join(f"{i+1} **{cog}**" for i, cog in enumerate(cogs))

        embed = Embed(
            title="Avaliable cogs",
            color=0x099,
            fields=[["Cogs:", numerical_cog_list, False]],
        )

        await interaction.followup.send(embed=embed)

        # Wait for message
        def check(m):
            return m.author == interaction.user and m.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out")
            return

        msg = int(msg.content)

        if msg == len(cogs):
            reloads_fail = ""
            reloads_success = ""

            for cog in cogs[:-2]:
                try:
                    if cog in self.bot.extensions:
                        await self.bot.unload_extension(cog)

                    await self.bot.load_extension(cog)
                    reloads_success += f"*{cog}*\n\n"
                except Exception as e:
                    reloads_fail += f"*{cog}*\nError: `{e}`\n\n"

            embed = Embed(
                title="Reload",
                color=0x099,
                fields=[
                    ["Reloaded successfully:", str(reloads_success)],
                    ["Failed to reload:", reloads_fail],
                ],
            )
            await interaction.followup.send(embed=embed)
            return
        else:
            cog = cogs[msg - 1]

        try:
            if cog in self.bot.extensions:
                await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
        except Exception as e:
            # create embed with error message
            embed = discord.Embed(title="Error", description=f"{e}", color=0x099CFF)
        else:
            # create embed with succesful announcement
            embed = discord.Embed(
                title="Reload", description=f"{cog} has been reloaded", color=0x099CFF
            )
        await interaction.followup.send(embed=embed)
