import discord
import time
import requests
import traceback

from typing import Optional
from datetime import datetime

from discord import app_commands
from discord.ext import commands

from botya.core.errors import DuplicateKey
from botya.core.utils.checks import is_premium
from botya.core.utils.invites import InviteTracker
from botya.core.utils.embed import Embed
from botya.core.utils.checks import user_has_permissions, bot_has_permissions
from botya.core.utils.helpers import check_uuid, bot_above, author_above
from botya.core.db.db import Database

from .helpers import LogSettingsActions, ClearMessagesTime
from .events import ModEvents


class Mod(
    ModEvents,
    commands.Cog,
    name="Moderation",
    description="for server moderators (kick, ban or other perms)",
):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracker = InviteTracker(bot)

    @app_commands.command(name="ban", description="Ban someone from the server.")
    @bot_has_permissions(ban_members=True)
    @user_has_permissions(ban_members=True)
    @app_commands.commands.guild_only()
    @app_commands.describe(
        user="The user to ban.",
        reason="The reason for the ban. Sent in DM to the user.",
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: Optional[str] = None,
    ):
        if user == interaction.guild.me:
            embed = Embed(
                "Action not possible",
                color=0xFF0000,
                description="It is impossible for me to ban myself, if i get in your way you can kick or ban me manually",
            )
            await interaction.response.send_message(embed=embed)
            return

        if not author_above(interaction.user, user, interaction.guild):
            embed = Embed(
                "I cannot let you do that. You are not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        if not bot_above(interaction.guild.me, user, interaction.guild):
            embed = Embed(
                "I cannot  do that. I am not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        try:
            getattr(interaction.guild, "icon")
            thum = interaction.guild.icon.url
        except AttributeError:
            thum = None

        user_embed = Embed(
            f"You were banned from {interaction.guild.name}!",
            0xFE0505,
            fields=[["Reason", f"`{reason}`"], ["Admin", interaction.user.mention]],
            thumbnail=thum,
            timestamp=True,
        )

        try:
            await user.send(embed=user_embed)
        except Exception:
            pass

        await interaction.guild.ban(user=user, reason=reason)

        guild_embed = Embed(
            title="",
            color=0xFFFFFF,
            description=f"{user.mention} was banned!",
            timestamp=True,
        )
        await interaction.response.send_message(embed=guild_embed)

    @app_commands.command(name="kick", description="Kick someone from the server.")
    @bot_has_permissions(kick_members=True)
    @user_has_permissions(kick_members=True)
    @app_commands.commands.guild_only()
    @app_commands.describe(
        user="The user to kick.",
        reason="The reason for the kick. Sent in DM to the user.",
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: Optional[str] = None,
    ):
        if user == interaction.guild.me:
            embed = Embed(
                "Action not possible",
                color=0xFF0000,
                description="It is impossible for me to ban myself, if i get in your way you can kick or ban me manually",
            )
            await interaction.response.send_message(embed=embed)
            return

        if not author_above(interaction.user, user, interaction.guild):
            embed = Embed(
                "I cannot let you do that. You are not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        if not bot_above(interaction.guild.me, user, interaction.guild):
            embed = Embed(
                "I cannot  do that. I am not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        try:
            getattr(interaction.guild, "icon")
            thum = interaction.guild.icon.url
        except AttributeError:
            thum = None

        user_embed = Embed(
            f"You were kicked from {interaction.guild.name}!",
            0xD78405,
            fields=[["Reason", f"`{reason}`"], ["Admin", interaction.user.mention]],
            thumbnail=thum,
            timestamp=True,
        )
        try:
            await user.send(embed=user_embed)
        except Exception:
            pass

        await interaction.guild.kick(user=user, reason=reason)

        guild_embed = Embed(
            title="",
            color=0xFFFFFF,
            description=f"{user.mention} was kicked!",
            timestamp=True,
        )
        await interaction.response.send_message(embed=guild_embed)

    @app_commands.command(
        name="softban", description="Bans and instantly unbans user (to clear messages)"
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(ban_members=True)
    @user_has_permissions(kick_members=True, delete_messages=True)
    @app_commands.describe(
        user="The user to softban.",
        reason="The reason for the softban. Sent in DM to the user.",
        delete_messages_time="The time bracket to delete messages from the user.",
    )
    async def softban(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        delete_messages_time: ClearMessagesTime,
        reason: Optional[str] = None,
    ):
        if user == interaction.guild.me:
            embed = Embed(
                "Action not possible",
                color=0xFF0000,
                description="It is impossible for me to ban myself, if i get in your way you can kick or ban me manually",
            )
            await interaction.response.send_message(embed=embed)
            return

        if not author_above(interaction.user, user, interaction.guild):
            embed = Embed(
                "I cannot let you do that. You are not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        if not bot_above(interaction.guild.me, user, interaction.guild):
            embed = Embed(
                "I cannot  do that. I am not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed)
            return

        try:
            getattr(interaction.guild, "icon")
            thum = interaction.guild.icon.url
        except AttributeError:
            thum = None

        user_embed = Embed(
            f"You were softbanned from {interaction.guild.name}!",
            0xD78405,
            fields=[["Reason", f"`{reason}`"], ["Admin", interaction.user.mention]],
            thumbnail=thum,
            timestamp=True,
        )
        try:
            await user.send(embed=user_embed)
        except Exception:
            pass

        await interaction.guild.ban(
            user=user, reason=reason, delete_message_seconds=delete_messages_time.value
        )
        await interaction.guild.unban(user=user, reason="Softban")

        guild_embed = Embed(
            title="",
            color=0xFFFFFF,
            description=f"{user.mention} Softbanned!",
            timestamp=True,
        )
        await interaction.response.send_message(embed=guild_embed)

    @app_commands.command(name="clear", description="Cleans messages from a channel.")
    @bot_has_permissions(manage_messages=True)
    @user_has_permissions(manage_messages=True)
    @app_commands.commands.guild_only()
    @app_commands.describe(
        number_of_messages="The number of messages to delete.",
        filter_by_user="The user to delete messages from. If not specified, all messages will be deleted.",
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        number_of_messages: int,
        filter_by_user: Optional[discord.Member],
    ):
        await interaction.response.defer(ephemeral=True)

        def check_user(message):
            return True if filter_by_user is None else message.author == filter_by_user

        deleted = await interaction.channel.purge(
            limit=number_of_messages, check=check_user
        )
        deleted = len(deleted)

        if filter_by_user is not None:
            member_message = f" from {filter_by_user.mention}"
        else:
            member_message = ""

        embed = Embed(
            title="", description=f"Deleted {deleted} messages{member_message}"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="log_settings", description="Cleans messages from a channel."
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(manage_messages=True)
    @user_has_permissions(manage_messages=True)
    @app_commands.describe(
        action="The action that you want to change settings for.",
        channel="The channel to set the log settings to.",
        active="Whether the log should be active or not.",
    )
    async def log_settings(
        self,
        interaction: discord.Interaction,
        action: LogSettingsActions,
        channel: Optional[discord.TextChannel],
        active: Optional[bool],
    ):
        await Database.set_log_settings(
            interaction.guild.id, action.value, channel, active
        )

        embed = Embed(
            title="Success",
            description=f"Logs for {action.value} will now be sent to {channel.mention}\nBut only if this action is active.",
            color=0x000000,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Gives a wrning to a user")
    @app_commands.commands.guild_only()
    @user_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user to warn.", reason="The reason for the warning"
    )
    async def warn(
        self, interaction: discord.Interaction, user: discord.Member, reason: str
    ):
        if user == interaction.user:
            embed = Embed(
                "Failure!",
                color=0xFF0000,
                description="You cannot warn yourself",
                footer=["Brought to you by Botya common sense AI™", ""],
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        elif user.bot:
            embed = Embed(
                "Failure!",
                color=0xFF0000,
                description="Why would you ever warn a bot?",
                footer=["Brought to you by Botya common sense AI™", ""],
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not author_above(interaction.user, user, interaction.guild):
            embed = Embed(
                "I cannot let you do that. You are not higher than the user in the role hierarchy.",
                color=0x000000,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        warn_id = await Database.create_warn(
            interaction.guild.id, user.id, interaction.user.id, reason
        )

        embed = Embed(
            "",
            color=0xBBBBBB,
            description=f"You succesfully warned {user.mention}\nWarn ID: `{warn_id}`",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="warn_list", description="Shows list of warnings for user/entire guild"
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user to show warnings for. If not specified, all warnings will be shown."
    )
    async def warn_list(
        self, interaction: discord.Interaction, user: Optional[discord.Member]
    ):
        if user:
            warns = await Database.get_warns(interaction.guild.id, user.id)
        else:
            warns = await Database.get_warns(interaction.guild.id)

        fields = []
        for warn in warns:
            user = interaction.guild.get_member(warn["user_id"])
            admin = interaction.guild.get_member(warn["admin_id"])

            user = user.mention if user else "**invalid(left?)**"
            admin = admin.mention if admin else "**invalid(left?)**"

            reason = warn["reason"]
            date = warn["created_at"][:-6]

            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
            date = int(round(time.mktime(date.timetuple()), 0))

            fields.append(
                [
                    warn["id"],
                    f"User: {user}\nAdmin: {admin}\nDate: <t:{date}>\n\nReason: ```{reason}```",
                ]
            )

        embed = Embed("", color=0x000000, description="", fields=fields)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="edit_warn",
        description="Allows admin to edit a warning reason (only the admin who gave the warning)",
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(kick_members=True)
    @app_commands.describe(
        warn_id="The ID of the warning to edit.",
        reason="The new reason for the warning.",
    )
    async def warn_edit(
        self, interaction: discord.Interaction, warn_id: str, reason: str
    ):
        uuid_valid = check_uuid(warn_id, 4)

        if not uuid_valid:
            await interaction.response.send_message(
                embed=Embed("", color=0xFF0000, description="Invalid `warn_id` format"),
                ephemeral=True,
            )
            return

        try:
            await Database.edit_warn(
                interaction.guild.id, interaction.user.id, warn_id, reason
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description=e), ephemeral=True
            )
            return

        await interaction.response.send_message(
            Embed("", description="Warning succesfully edited"), ephemeral=True
        )

    @app_commands.command(
        name="remove_warn", description="Allows admin to edit a delete a warning"
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(administrator=True)
    @app_commands.describe(warn_id="The ID of the warning to delete.")
    async def warn_remove(self, interaction: discord.Interaction, warn_id: str):
        uuid_valid = check_uuid(warn_id, 4)

        if not uuid_valid:
            await interaction.response.send_message(
                embed=Embed("", color=0xFF0000, description="Invalid `warn_id` format"),
                ephemeral=True,
            )
            return

        try:
            await Database.delete_warn(interaction.guild.id, warn_id)
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description=e), ephemeral=True
            )
            return

        await interaction.response.send_message(
            Embed("", description="Warning succesfully deleted")
        )

    """ Group for autoroles """

    autorole = app_commands.Group(
        name="autorole",
        description="Settings for autoroles (roles that members get instantly after joining)",
        guild_only=True,
    )

    @autorole.command(name="add", description="Adds a role to autorole list")
    @user_has_permissions(administrator=True)
    @bot_has_permissions(manage_roles=True)
    @app_commands.describe(role="Role to add to autorole list (select from list)")
    async def autorole_add(self, interaction: discord.Interaction, role: discord.Role):
        try:
            await Database.add_autorole(interaction.guild.id, role)
        except DuplicateKey as e:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description=e), ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=Embed(
                title="",
                color=0xAAC9AA,
                description=f"{role.mention} is now an autorole",
            )
        )

    @autorole.command(name="remove", description="Removes a role from autorole list")
    @user_has_permissions(administrator=True)
    @app_commands.describe(role="Role to add to autorole list (select from list)")
    async def autorole_remove(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        try:
            await Database.remove_autorole(interaction.guild.id, role)
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description=e), ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=Embed(
                title="",
                color=0xAAC9AA,
                description=f"{role.mention} is no longer an autorole",
            )
        )

    @app_commands.command(
        name="show_server_settings", description="Shows all server settings"
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(manage_guild=True)
    async def show_server_settings(self, interaction: discord.Interaction):
        settings = await Database.get_guild_settings(interaction.guild.id)
        autoroles = await Database.get_autoroles(interaction.guild.id)
        roles = [interaction.guild.get_role(role) for role in autoroles]

        roles_str = "".join(
            f"{role.mention} (`{role.id}`)\n" if role else "`deleted role`\n"
            for role in roles
        )
        acts = [act.value for act in LogSettingsActions]

        welcome_channel = interaction.guild.get_channel(settings["welcome_channel"])
        welcome_message = settings["welcome_message"]
        welcome_active = "active" if settings["welcome_active"] else "inactive"

        if welcome_message:
            welcome_message = welcome_message.replace(
                "[user]", interaction.user.mention
            )
            welcome_message = welcome_message.replace(
                "[userName]", interaction.user.name
            )
            welcome_message = welcome_message.replace(
                "[memberCount]", str(len(interaction.guild.members))
            )
            welcome_message = welcome_message.replace(
                "[server]", interaction.user.guild.name
            )
            welcome_message = welcome_message.replace("[nl]", "\n")

        timezone = settings["timezone"]

        welcome_channel = getattr(welcome_channel, "mention", "no channel")

        text = f"`channel:` {welcome_channel}\n"
        text += f"`message:` {welcome_message}"

        text_2 = ""
        for act in acts:
            channel = interaction.guild.get_channel(settings[act])
            active = settings[f"{act}_active"]

            acte = act.replace("_", " ")

            try:
                text_2 += f"`{acte}` {channel.mention} `{active}`\n"
            except Exception:
                text_2 += f"`{acte}` no_channel `{active}`\n"

        embed = Embed(
            f"**{interaction.guild.name}** settings",
            author=[
                f"{interaction.user.name}#{interaction.user.discriminator}",
                interaction.user.avatar.url,
            ],
            fields=[
                [f"Welcome message (`{welcome_active}`)", text, False],
                ["Time zone", f"`{timezone}`", False],
                ["Autorole (joinroles)", roles_str, False],
                ["Logs", text_2, False],
            ],
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="copy_emoji",
        description="Copies an emoji from another server (you probably need nitro)",
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(manage_emojis=True)
    @bot_has_permissions(manage_emojis=True)
    @app_commands.describe(
        emojis="Emoji(s) (don't separate) to copy (select from list on right)"
    )
    async def copy_emoji(self, interaction: discord.Interaction, emojis: str):
        await interaction.response.defer()

        emojis = emojis.split(">")

        del emojis[-1]

        emj = []

        for emoji in emojis:
            emoji = emoji.strip()
            emoji = emoji.strip(" ")
            emoji = emoji.strip("<>")
            emoji = emoji.split(":")
            emj.append(emoji)

        emojis = []

        # add emoji
        try:
            for emoji in emj:
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji[-1]}"
                emoji_name = emoji[-2]

                response = requests.get(emoji_url)
                emoji = await interaction.guild.create_custom_emoji(
                    name=emoji_name,
                    image=response.content,
                    reason=f"Emoji copied by {interaction.user.name}#{interaction.user.discriminator}",
                )

                emojis.append(emoji)
            # all emojis to str
            emojis = " ".join([str(emoji) for emoji in emojis])

            await interaction.followup.send(
                embed=Embed(
                    "",
                    color=0xAAC9AA,
                    description=f"Emoji(s) {emojis} succesfully added",
                )
            )
        except Exception:
            traceback.print_exc()
            await interaction.followup.send(
                embed=Embed("", color=0x880000, description="Could not add emoji"),
                ephemeral=True,
            )
            return

    @app_commands.command(
        name="embed", description="Allows server moderators to send embeds"
    )
    @app_commands.commands.guild_only()
    @is_premium()
    @user_has_permissions(manage_guild=True)
    @app_commands.describe()
    @app_commands.describe(
        color="Embed color (in decimal)",
        author_name="Author name",
        author_icon="Author icon (url)",
        title="Embed title",
        description="Embed description",
        footer="Embed footer",
        footer_icon="Embed footer icon (url)",
        image="Embed image (url)",
        thumbnail="Embed thumbnail (url)",
        field_1_name="Field 1 title",
        field_1_value="Field 1 value",
        field_2_name="Field 2 title",
        field_2_value="Field 2 value",
        field_3_name="Field 3 title",
        field_3_value="Field 3 value",
        field_4_name="Field 4 title",
        field_4_value="Field 4 value",
        field_5_name="Field 5 title",
        field_5_value="Field 5 value",
        field_6_name="Field 6 title",
        field_6_value="Field 6 value",
        timestamp="Do you want a timestamp? (yes/no)",
    )
    async def embed(
        self,
        interaction: discord.Interaction,
        color: Optional[app_commands.Range[int, 0, 16777215]],
        author_name: Optional[app_commands.Range[str, 0, 256]],
        author_icon: Optional[str],
        title: Optional[app_commands.Range[str, 0, 256]],
        description: Optional[app_commands.Range[str, 0, 2048]],
        footer: Optional[app_commands.Range[str, 0, 2048]],
        footer_icon: Optional[str],
        image: Optional[str],
        thumbnail: Optional[str],
        field_1_name: Optional[app_commands.Range[str, 0, 256]],
        field_1_value: Optional[app_commands.Range[str, 0, 2048]],
        field_2_name: Optional[app_commands.Range[str, 0, 256]],
        field_2_value: Optional[app_commands.Range[str, 0, 2048]],
        field_3_name: Optional[app_commands.Range[str, 0, 256]],
        field_3_value: Optional[app_commands.Range[str, 0, 2048]],
        field_4_name: Optional[app_commands.Range[str, 0, 256]],
        field_4_value: Optional[app_commands.Range[str, 0, 2048]],
        field_5_name: Optional[app_commands.Range[str, 0, 256]],
        field_5_value: Optional[app_commands.Range[str, 0, 2048]],
        field_6_name: Optional[app_commands.Range[str, 0, 256]],
        field_6_value: Optional[app_commands.Range[str, 0, 2048]],
        timestamp: Optional[bool],
    ):
        embed = discord.Embed(color=color, title=title, description=description)

        if (
            not title
            and not (description)
            and not (field_1_name and field_1_value)
            and not (author_name and author_icon)
            and not (footer)
            and not (image)
            and not (thumbnail)
        ):
            await interaction.response.send_message(
                embed=Embed(
                    "",
                    color=0x880000,
                    description="You need to specify at least one of the following: title, description, field (title and content), author (and author_icon), footer, image, thumbnail",
                ),
                ephemeral=True,
            )
            return

        if author_name and author_icon:
            embed.set_author(name=author_name, icon_url=author_icon)

        if footer and footer_icon:
            embed.set_footer(text=footer, icon_url=footer_icon)
        elif footer:
            embed.set_footer(text=footer)

        if timestamp:
            embed.timestamp = datetime.utcnow()

        if image:
            embed.set_image(url=image)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if field_1_name and field_1_value:
            embed.add_field(name=field_1_name, value=field_1_value)

        if field_2_name and field_2_value:
            embed.add_field(name=field_2_name, value=field_2_value)

        if field_3_name and field_3_value:
            embed.add_field(name=field_3_name, value=field_3_value)

        if field_4_name and field_4_value:
            embed.add_field(name=field_4_name, value=field_4_value)

        if field_5_name and field_5_value:
            embed.add_field(name=field_5_name, value=field_5_value)

        if field_6_name and field_6_value:
            embed.add_field(name=field_6_name, value=field_6_value)

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Done:tada:", ephemeral=True)
