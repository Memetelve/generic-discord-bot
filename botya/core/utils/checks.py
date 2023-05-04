from typing import Callable, TypeVar
from datetime import datetime

import discord

from discord.app_commands.commands import check
from botya.core.utils.types import tz
from botya.core.errors import MissingPremium
from discord.app_commands.errors import BotMissingPermissions, MissingPermissions

T = TypeVar("T")


def user_has_permissions(**perms: bool):
    def predicate(interaction: discord.Interaction):
        if (
            interaction.user.guild_permissions.administrator
            or interaction.user == interaction.guild.owner
        ):
            return True
        if all(
            getattr(interaction.user.guild_permissions, perm, None) == value
            for perm, value in perms.items()
        ):
            return True
        missing = []
        for perm, value in perms.items():
            x = getattr(interaction.user.guild_permissions, perm, None) == value
            if not x:
                missing.append(perm)

        raise MissingPermissions(missing)

    return check(predicate)


def bot_has_permissions(**perms: bool) -> Callable[[T], T]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild.me.guild_permissions.administrator:
            return True

        permissions = interaction.app_permissions
        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return check(predicate)


def is_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != 288717325765443587:
            raise MissingPermissions("You do not own this bot.")
        return True

    return check(predicate)


def is_guild_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner.id:
            raise MissingPermissions("You do not own this guild.")
        return True

    return check(predicate)


def is_premium(tier: int = 1):
    async def predicate(interaction: discord.Interaction):
        from botya import premium_ent

        if ent := premium_ent.get(interaction.user.id):
            if (ent["premium_tier"] >= tier) and (
                ent["premium_until"] > datetime.now(tz=tz)
            ):
                return True

        raise MissingPremium(f"You do not have premium tier {tier}")

    return check(predicate)
