import os
import json
import logging
import traceback

import discord
from discord.ext import commands
from botya.core.errors import MissingPremium
from botya.config import BUY_PREMIUM_LINK

import botya
from botya.core.utils.embed import Embed
from botya.core.utils.views import (
    DefaultRoleView,
    DefaultRoleButton,
    TicketView,
    TicketButton,
    TicketMessageView,
    TicketCloseButton,
    TicketOpenButton,
    TicketDeleteButton,
    NewGPTConversationView,
    NewGPTConversationButton,
    BuyPremiumView,
    BuyPremiumButton,
)
from botya.core.db.db import Database

handler = logging.FileHandler(filename="botya.log", encoding="utf-8", mode="a")
logger = logging.getLogger("discord")
logger.addHandler(handler)

with open("config.json", "r") as f:
    config = json.load(f)

    PREFIX = config["prefix"]
    BOT_NAME = config["bot_name"]

    if os.name != "nt":
        TOKEN = config["token_botya"]
        APP_ID = config["app_id_botya"]
    else:
        TOKEN = config["token_alpha"]
        APP_ID = config["app_id_alpha"]

    DEBUG: bool = config["debug"]
    UPDATE: bool = config["update_discord"]

    extensions = config["cogs"]


class Botya(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=discord.Intents.all(),
            application_id=APP_ID,
            help_command=None,
        )

    async def setup_hook(self):
        roles = await Database.get_reation_roles()
        view = DefaultRoleView()

        for iter, role in enumerate(roles):
            role = role["role_id"]
            role = str(role)

            # max 25 buttons per view
            if iter % 25 == 0 and iter != 0:
                self.add_view(view)
                view = DefaultRoleView()

            view.add_item(DefaultRoleButton(role))

        if len(view.children) > 0:
            self.add_view(view)

        view = TicketView()
        view.add_item(TicketButton())
        self.add_view(view)

        view = NewGPTConversationView()
        view.add_item(NewGPTConversationButton())
        self.add_view(view)

        view = TicketMessageView()
        view.add_item(TicketCloseButton())
        view.add_item(TicketOpenButton())
        view.add_item(TicketDeleteButton())
        self.add_view(view)

        for ext in extensions:
            try:
                await self.load_extension(f"botya.cogs.{ext}")
            except Exception:
                traceback.print_exc()

        if UPDATE:
            await bot.tree.sync(guild=discord.Object(id=790337229532299320))
            await bot.tree.sync(guild=discord.Object(id=815649625104711720))
            await bot.tree.sync(guild=discord.Object(id=1040352846182359122))

            if not botya.DEBUG:
                await bot.tree.sync()

    async def on_ready(self):
        print(f"{self.user} has connected to discord")


bot = Botya()
tree = bot.tree


@bot.event
async def on_command_error(ctx, error):
    pass


@bot.event
async def on_app_command_completion(interaction, command):
    guild = getattr(interaction, "guild", None)
    guild_id = guild.id if guild else None

    logger.info(f'{interaction.user} used "{command.name}" on {guild}({guild_id})')


@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    guild = getattr(interaction, "guild", None)
    guild_id = guild.id if guild else None

    logger.info(
        f'{interaction.user} used (and failed) "{interaction.command.name}" on {guild}({guild_id})'
    )

    user = interaction.user

    if isinstance(error, MissingPremium):
        embed = Embed(
            color=0xCE2020,
            description=f"{user.mention}, you need premium to use this command",
        )

        view = BuyPremiumView()
        view.add_item(
            BuyPremiumButton(
                label="Buy premium",
                style=discord.ButtonStyle.url,
                url=BUY_PREMIUM_LINK,
            )
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    elif isinstance(error, discord.app_commands.errors.MissingPermissions):
        if type(error.missing_permissions) == list:
            perms = "".join(f"{perm}, " for perm in error.missing_permissions)
            text = f"You miss `{perms}` permissions"
        elif type(error.missing_permissions) == str:
            text = error.missing_permissions
        else:
            text = "You miss permissions"

        embed = Embed(
            title=f"{user.name}, You do not have permission to use this command!",
            color=0xCE2020,
            description=text,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, discord.app_commands.errors.BotMissingPermissions):
        perms = "".join(f"{perm}, " for perm in error.missing_permissions)
        embed = Embed(
            title=f"{user.name}, I do not have permission to use this command!",
            color=0xCE2020,
            description=f"I miss `{perms}` permissions\n\nif you believe this is an error check my permissions or contact server admin",
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif not isinstance(error, discord.app_commands.errors.CommandNotFound):
        traceback.print_exc()


try:
    bot.run(TOKEN, log_handler=handler)
except KeyboardInterrupt:
    print("KeyboardInterrupt")
    bot.loop.run_until_complete(bot.logout())
    bot.loop.run_until_complete(bot.close())
    bot.loop.close()
