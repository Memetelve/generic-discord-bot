import discord
import traceback
import requests
import json

from discord import app_commands
from discord.ext import commands

from difflib import SequenceMatcher  # black magic for comparing strings

from botya.core.utils.checks import user_has_permissions
from botya.core.utils.embed import Embed
from botya.core.db.db import Database

from .tasks import ClashOfClansTasks

# get coc_api fron config.json
with open("config.json", "r") as f:
    config = json.load(f)
    coc_token = config["coc_api"]


class Clash(
    ClashOfClansTasks,
    commands.Cog,
    name="Clash of Clans",
    description="Commands for game Clash of Clans",
):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.check_clash_of_clans_wars.start()

    @app_commands.command(
        name="check_coc_clan_members",
        description="Shows which members of the server are in the clan",
    )
    @user_has_permissions(manage_guild=True)
    @app_commands.describe(clan_tag="Clan tag ()")
    async def check_coc_clan(self, interaction: discord.Interaction, clan_tag: str):
        clan_tag = clan_tag.replace("#", "").capitalize()

        try:
            # api request
            url = f"https://api.clashofclans.com/v1/clans/%23{clan_tag}/members"
            headers = {"Authorization": f"Bearer {coc_token}"}
            # get clan members using requests
            r = requests.get(url, headers=headers)
            # get json
            members = r.json()

            # get ctx.guild members
            guild_members = interaction.guild.members

            matched_users = []
            unmatched_users = []

            for discord_user in guild_members:
                if discord_user.bot:
                    continue

                is_found = False

                for api_member in members["items"]:
                    api_name = api_member["name"].lower()
                    discord_nick = discord_user.nick
                    if discord_nick is None:
                        discord_nick = discord_user.name
                    discord_nick = discord_nick.lower()

                    name_similarity = SequenceMatcher(
                        a=str(api_name), b=str(discord_nick)
                    ).ratio()

                    if name_similarity > 0.8:
                        matched_users.append(discord_user)
                        is_found = True
                        break

                if not is_found:
                    unmatched_users.append(discord_user)

            unfound_clan_members = []

            for api_member in members["items"]:
                api_name = api_member["name"]

                for found_discord_user in matched_users:
                    discord_nick = found_discord_user.nick
                    if discord_nick is None:
                        discord_nick = found_discord_user.name
                    discord_nick = discord_nick.lower()

                    name_similarity = SequenceMatcher(
                        a=str(api_name.lower()), b=str(discord_nick)
                    ).ratio()

                    if name_similarity > 0.8:
                        break
                else:
                    unfound_clan_members.append(api_name)

            # create embed with matched and unmatched, use Embed
            len_matched = len(matched_users)
            len_unmatched = len(unmatched_users)
            len_clan_members_not_found = len(unfound_clan_members)

            matched = "".join(f"{user.mention}\n" for user in matched_users)
            unmatched = "".join(f"{user.mention}\n" for user in unmatched_users)
            clan_members_not_found = "".join(
                f"{name}\n" for name in unfound_clan_members
            )

            embed = Embed(
                title="Clash of Clans Clan Members",
                description=f"Clan: {clan_tag}",
                fields=[
                    [f"Matched with clan members: {len_matched}", matched, False],
                    [f"Unmatched with clan members: {len_unmatched}", unmatched, False],
                    [
                        f"Clan members not found on discord: {len_clan_members_not_found}",
                        clan_members_not_found,
                        False,
                    ],
                ],
                footer=[
                    "This info excludes bots",
                    interaction.guild.me.avatar.url,
                ],
            )
            await interaction.response.send_message(embed=embed)
        except Exception:
            await interaction.response.send_message("Error")
            traceback.print_exc()

    @app_commands.command(name="add_war_notifier", description="Adds war notifications")
    @user_has_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.describe(
        clan_tag="Clash of clans tag",
        channel="Channel where notifications will be sent",
        active="should the notifications be active",
    )
    async def add_war_notifier(
        self,
        interaction: discord.Interaction,
        clan_tag: str,
        channel: discord.TextChannel,
        active: bool,
    ):
        # add war notifier to db
        await Database.set_war_notifier(
            interaction.guild.id, channel.id, clan_tag, active
        )

        # send message
        embed = Embed("War notification setting saved", 0x000)

        await interaction.response.send_message(embed=embed)
