import discord
import re
import pytz
import json

from typing import Optional

from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from botya.core.db.db import Database
from botya.core.utils.invites import InviteTracker
from botya.core.utils.embed import Embed
from botya.core.utils.checks import (
    user_has_permissions,
    bot_has_permissions,
    is_guild_owner,
)
from botya.core.utils.helpers import is_emoji
from botya.core.utils.views import (
    DefaultRoleView,
    DefaultRoleButton,
    TicketView,
    TicketButton,
)

from .events import AdminEvents


styles = [
    ["", "", "", ""],
    ["[", "]", "", ""],
    ["", "|", "", ""],
    ["【", "】", "", ""],
    ["", "»", "", ""],
    ["〖", "〗", "", ""],
    ["〔", "〕", "", ""],
    ["", "", "「", "」"],
    ["", "", "『", "』"],
    ["┊", "・", "", ""],
]

emojis = {
    "General": "🌍",
    "Announcements": "📣",
    "Introductions": "🤝",
    "Off-topic": "💬",
    "Gaming": "🎮",
    "Music": "🎵",
    "Art": "🎨",
    "Memes": "🤣",
    "Sports": "🏀",
    "Movies": "🎬",
    "TV shows": "📺",
    "Books": "📚",
    "Writing": "📝",
    "Photography": "📷",
    "Programming": "💻",
    "Anime": "🍥",
    "Food": "🍔",
    "Fitness": "💪",
    "Politics": "🗳️",
    "Science": "🔬",
    "Technology": "🤖",
    "Travel": "🌴",
    "Fashion": "👗",
    "Beauty": "💄",
    "Pets": "🐶",
    "Feedback": "📩",
    "Events": "🎉",
    "Advertising": "📢",
    "Study": "📚",
    "Homework": "📝",
    "Debate": "🗣️",
    "Language Exchange": "🗨️",
    "Social Media": "📱",
    "Bot Commands": "🤖",
    "Roleplay": "🎭",
    "Voice Chat": "🎤",
    "Text Chat": "💬",
    "NSFW": "🔞",
    "Help Desk": "🆘",
    "Community Events": "🎊",
    "Q&A": "💬",
    "Podcasts": "🎙️",
    "Gaming News": "🎮",
    "Achievements": "🏆",
    "Tips and Tricks": "🎓",
    "Science Fiction": "🚀",
    "Fantasy": "🧙",
    "Music Production": "🎧",
    "Education": "🎓",
    "Video Production": "🎥",
    "Charity": "💰",
    "Entrepreneurship": "💼",
    "Mental Health": "🧠",
    "History": "📜",
    "Environment": "🌳",
    "Philosophy": "🤔",
    "Cryptocurrency": "💰",
    "Design": "🎨",
    "Admin": "👑",
    "Mod Lounge": "🛋️",
    "Rules": "📜",
    "Info": "ℹ️",
    "Suggestions": "🤔",
    "Report": "🚨",
    "Applications": "📝",
    "Welcome": "🎉",
    "Farewell": "👋",
    "News": "📰",
    "Updates": "📣",
    "Server Status": "🟢",
    "Server Logs": "📊",
    "Emotes": "😂",
    "Bots": "🤖",
    "Verification": "✅",
    "Polls": "🗳️",
    "Partner": "🤝",
    "Donations": "💰",
    "Shop": "🛍️",
    "Giveaways": "🎁",
    "VIP": "🌟",
    "Premium": "💎",
    "Archive": "📦",
    "Backups": "📂",
    "Development": "🛠️",
    "Testing": ",🧪",
    "Bugs": "🐛",
    "Verify": "🔑",
    "Bot": "🤖",
    "Mod": "🛡️",
    "Support": "📞",
    "Log": "📂",
    "Ticket": "🎫",
    "Voice": "🎙️",
    "Text": "💬",
    "Music": "🎵",
    "AFK": "🌴",
    "Private": "🔒",
    "Public": "🔓",
    "Game": "🎮",
}


async def create_channel(guild: discord.Guild, channel, ovrs, category=None):
    if channel["type"] == 0:
        return await guild.create_text_channel(
            channel["name"], overwrites=ovrs, category=category, topic=channel["topic"]
        )
    elif channel["type"] == 2:
        return await guild.create_voice_channel(
            channel["name"], overwrites=ovrs, category=category
        )
    elif channel["type"] == 5:
        return await guild.create_text_channel(
            channel["name"],
            overwrites=ovrs,
            category=category,
            topic=channel["topic"],
            news=True,
        )
    elif channel["type"] == 13:
        return await guild.create_stage_channel(
            channel["name"], overwrites=ovrs, category=category, topic=channel["topic"]
        )
    elif channel["type"] == 15:
        return await guild.create_forum(
            channel["name"], overwrites=ovrs, category=category, topic=channel["topic"]
        )


def edit_channel_name(name, style):
    regex = re.compile(
        "(["
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "])"
    )
    emoji = re.search(regex, name)
    if emoji:
        index = name.find(emoji[0])
        emoji = name[index]
    else:
        emoji = ""

    regex = re.compile("[\d]")

    regex = re.compile("[^\w.\- ]")
    name = re.sub(regex, "", name)

    if emoji == "" and style != 0:
        for key in emojis.keys():
            if key.lower() in name.lower():
                emoji = emojis[key]

    if style == 0:
        emoji = ""

    name = (
        styles[style][0]
        + emoji
        + styles[style][1]
        + styles[style][2]
        + name
        + styles[style][3]
    )

    return name


class Admin(
    AdminEvents,
    commands.Cog,
    name="Administration",
    description="for server administrators (admin perms)",
):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracker = InviteTracker(bot)

    @app_commands.command(
        name="server_look", description="Change how your server look in a single click"
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    @app_commands.choices(
        style=[
            Choice(name="Text", value=1),
            Choice(name="🍍 | Text", value=3),
            Choice(name="【🍍】Text", value=4),
            Choice(name="〔🍍〕Text", value=7),
            Choice(name="[🍍] Text", value=2),
            Choice(name="【🍍】Text", value=4),
            Choice(name="〖🍍〗Text", value=6),
            Choice(name="〔🍍〕Text", value=7),
            Choice(name="🍍「Text」", value=8),
            Choice(name="🍍『Text』", value=9),
            Choice(name="┊🍍・getting-started", value=10),
        ]
    )
    @app_commands.describe(
        style="The style of the channel/category names",
        category="Only channeles in this category will be changed",
        channel_type="Only channels of this type will be changed",
    )
    async def server_look(
        self,
        interaction: discord.Interaction,
        style: Choice[int],
        category: Optional[discord.CategoryChannel],
        channel_type: Optional[discord.ChannelType],
    ):
        await interaction.response.defer()

        style = style.value - 1

        no = 0

        if category:
            for cat in interaction.guild.categories:
                if cat == category:
                    name = cat.name
                    name = edit_channel_name(name, style)
                    await cat.edit(name=name)
                    no += 1

        if not category:
            category = interaction.guild

        for channel in category.channels:
            if channel.type != channel_type and channel_type:
                continue

            name = channel.name
            name = edit_channel_name(name, style)
            await channel.edit(name=name)
            no += 1

        embed = Embed(
            "", 0xDFDFDF, description=f"Succesfully modified name of {no} channels"
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="welcome_message",
        description="Set a message that is sent when someone join the server",
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    @app_commands.describe(
        message="placeholders: [user] - mention user\n[userName] - username (no mention)\n[memberCount] - server member count (with bots)\n[inviter] - mention creator of invite\n [inviterName] - inviter without mention\n[inviteCount] - amount of real invites for inviter\n[server] - server name\n[nl] - go to new line",
        channel="The channel where the message will be sent",
        active="If the welcome message is active",
    )
    async def welcome_message(
        self,
        interaction: discord.Interaction,
        message: Optional[str],
        channel: Optional[discord.TextChannel],
        active: Optional[bool],
    ):
        await Database.set_welcome_message(
            interaction.guild.id, channel.id, message, active
        )

        embed = Embed(title="Success", description="Changes saved", color=0x000000)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="create_quiet_role",
        description="Creates a role with removed permission to send messages/speak in every channel",
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    async def create_quiet_role(self, interaction: discord.Interaction):
        await interaction.response.defer()
        place = interaction.guild.me.top_role.position - 1

        role = await interaction.guild.create_role(name="🔇quiet", color=0x2F3136)
        await role.edit(position=place)

        for channel in interaction.guild.channels:
            try:
                await channel.set_permissions(
                    role,
                    send_messages=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False,
                    use_application_commands=False,
                    speak=False,
                    stream=False,
                    add_reactions=False,
                    request_to_speak=False,
                    change_nickname=False,
                )
            except Exception:
                pass

        embed = Embed(description=f"Created quiet role: {role.mention}")
        await interaction.followup.send(embed=embed)

    reaction_role = app_commands.Group(
        name="reaction_role", description="Settings for reaction roles", guild_only=True
    )

    @reaction_role.command(
        name="setup",
        description="Send a message that will act as a base for other reactionrole commands",
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    @app_commands.describe(
        text="Use [nl] for newline",
        embed="Do you want the bot to use embed or normal text?",
    )
    async def setup(
        self, interaction: discord.Interaction, text: str, embed: bool = False
    ):
        view = DefaultRoleView()

        text = text.replace("[nl]", "\n")

        if not embed:
            await interaction.channel.send(text, view=view)
        else:
            embed = Embed(title="", description=text)
            await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Done!🎉🎉🎉", ephemeral=True)

    @reaction_role.command(
        name="add", description="Add a button with assinged role to base message"
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    @app_commands.describe(
        message_id="ID of bots message that you want to add reaction role to",
        role="Role that will be assigned/removed to/from user after clicking",
        emoji="Emoji that will be used for reaction (max one )",
    )
    async def add(
        self,
        interaction: discord.Interaction,
        message_id: str,
        role: discord.Role,
        label: str,
        emoji: str = "",
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        message = await interaction.channel.fetch_message(int(message_id))

        if len(emoji) > 1:
            emoji = emoji[0]

        if emoji == "":
            emoji = None

        if not is_emoji(emoji):
            await interaction.response.send_message(
                "Your emoji should be emoji (on none) not other text", ephemeral=True
            )
            return

        view = DefaultRoleView()
        for comp in message.components:
            for child in comp.children:
                try:
                    if child.custom_id == str(role.id):
                        continue

                    view.add_item(
                        DefaultRoleButton(
                            style=child.style,
                            label=child.label,
                            emoji=child.emoji,
                            custom_id=child.custom_id,
                        )
                    )

                except TypeError as e:
                    print(e)

        await Database.add_reaction_role(role.id)
        view.add_item(
            DefaultRoleButton(
                style=style, label=label, emoji=emoji, custom_id=str(role.id)
            )
        )

        try:
            embed = message.embeds[0]
        except Exception:
            embed = None
        await message.edit(content=message.content, embed=embed, view=view)

        await interaction.response.send_message("Done!🎉🎉🎉", ephemeral=True)

    @reaction_role.command(
        name="remove",
        description="Remove a button with assinged role from base message",
    )
    @app_commands.commands.guild_only()
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    @app_commands.describe(
        message_id="ID of bots message that you want to remove reaction role from",
        role="Role(and button) that will be removed from message",
    )
    async def remove(
        self, interaction: discord.Interaction, message_id: str, role: discord.Role
    ):
        message = await interaction.channel.fetch_message(int(message_id))

        view = DefaultRoleView()
        for comp in message.components:
            for child in comp.children:
                if child.custom_id != str(role.id):
                    view.add_item(
                        DefaultRoleButton(
                            style=child.style,
                            label=child.label,
                            emoji=child.emoji,
                            custom_id=child.custom_id,
                        )
                    )
                else:
                    edited = True

        if not edited:
            await interaction.response.send_message(
                f"Button for {role.mention} was never created", ephemeral=True
            )
            return

        try:
            embed = message.embeds[0]
        except Exception:
            embed = None
        await message.edit(content=message.content, embed=embed, view=view)

        await interaction.response.send_message("Done!🎉🎉🎉", ephemeral=True)

    @app_commands.command(
        name="set_timezone",
        description="Let the bot know how to set time in all messages sent here",
    )
    @app_commands.commands.guild_only()
    @user_has_permissions(administrator=True)
    @app_commands.describe(
        time_zone='Your server\'s time zone. Formated like "Continent/City" example: Europe/Berlin'
    )
    async def set_timezone(self, interaction: discord.Interaction, time_zone: str):
        user = interaction.user
        try:
            timezone = pytz.timezone(time_zone)
        except Exception:
            embed = Embed(
                description="Supplied timezone does not match format/is not a real timezone"
            )
            await interaction.response.send_message(embed=embed)
            return

        await Database.set_timezone(interaction.guild.id, timezone.zone)

        embed = Embed(
            description=f"This servers timezone was set to {timezone.zone}",
            color=0x2EC2B3,
            author=[f"{user.name}#{user.discriminator}", user.avatar.url],
        )
        await interaction.response.send_message(embed=embed)

    tickets = app_commands.Group(
        name="tickets", description="Settings for tickets", guild_only=True
    )

    @tickets.command(
        name="setup", description="Setup tickets (create 2 categories and send message)"
    )
    @user_has_permissions(administrator=True)
    @app_commands.describe()
    async def ticket_setup(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild

        overwrites_closed = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False, send_messages=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                manage_roles=True,
            ),
        }
        overwrites_open = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                manage_roles=True,
            ),
        }
        overwrites_channel = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                manage_roles=True,
            ),
        }

        category = await guild.create_category(
            "Open Tickets", overwrites=overwrites_open
        )
        category2 = await guild.create_category(
            "Closed Tickets", overwrites=overwrites_closed
        )

        channel = await guild.create_text_channel(
            "〔🎫〕tickets", overwrites=overwrites_channel
        )

        await Database.set_tickets(guild.id, category.id, category2.id)

        # send message to tickets channel with button
        view = TicketView()
        view.add_item(
            TicketButton(
                label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫"
            )
        )

        embed = Embed(
            title="Tickets",
            description="Click the button below to open a ticket",
            color=0x2EC2B3,
        )
        await channel.send(embed=embed, view=view)

        embed = Embed(
            description=f"Tickets are now setup! Use `/ticket create` or click a button in {channel.mention} to create a ticket"
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="save_server",
        description="Save the state of the server. Channnels, roles, categories and permissions",
    )
    @app_commands.guild_only()
    @app_commands.describe(note="Note to add to the saved server")
    @user_has_permissions(administrator=True)
    @bot_has_permissions(administrator=True)
    async def save_server(self, interaction: discord.Interaction, note: str = None):
        # sourcery skip: merge-dict-assign, move-assign-in-block

        guild_save = {"roles": [], "channels": [], "categories": []}

        guild: discord.Guild = interaction.guild
        channel: discord.abc.GuildChannel = interaction.channel

        channels = await guild.fetch_channels()
        roles = await guild.fetch_roles()

        roles_saved = []

        for role in roles:
            if role.managed:
                continue

            dic = {
                "name": "🉥" if role.is_default() else role.name,
                "id": role.id,
                "position": role.position,
                "color": role.color.value,
                "mentionable": role.mentionable,
                "hoist": role.hoist,
                "permissions": role.permissions.value,
            }
            roles_saved.append(dic)

        roles_saved = sorted(roles_saved, key=lambda k: k["position"], reverse=True)

        guild_save["roles"] = roles_saved
        del roles_saved

        no_cat_channels = []
        for channel in channels:
            if (
                channel.category is None
                and channel.type != discord.ChannelType.category
            ):
                role_ovs = {}

                for ov in channel.overwrites:
                    if isinstance(ov, discord.Role):
                        role_ovs[ov.id] = {
                            "allow": channel.overwrites[ov].pair()[0].value,
                            "deny": channel.overwrites[ov].pair()[1].value,
                        }

                dic = {
                    "name": channel.name,
                    "topic": getattr(channel, "topic", None),
                    "position": channel.position,
                    "type": channel.type.value,
                    "overwrites": role_ovs,
                }
                no_cat_channels.append(dic)

        no_cat_channels = sorted(no_cat_channels, key=lambda x: x["position"])
        guild_save["channels"] = no_cat_channels

        categories = []

        for cat in channels:
            if cat.type != discord.ChannelType.category:
                continue

            chnls = []
            for channel in cat.channels:
                # permissions for channel in category
                role_ovs = {}
                for ov in channel.overwrites:
                    if isinstance(ov, discord.Role):
                        role_ovs[ov.id] = {
                            "allow": channel.overwrites[ov].pair()[0].value,
                            "deny": channel.overwrites[ov].pair()[1].value,
                        }

                dic = {
                    "name": channel.name,
                    "topic": getattr(channel, "topic", None),
                    "position": channel.position,
                    "type": channel.type.value,
                    "overwrites": role_ovs,
                }
                chnls.append(dic)

            # permissions for category
            role_ovs = {}
            for ov in cat.overwrites:
                if isinstance(ov, discord.Role) and not getattr(ov, "managed", True):
                    role_ovs[ov.id] = {
                        "allow": cat.overwrites[ov].pair()[0].value,
                        "deny": cat.overwrites[ov].pair()[1].value,
                    }

            categories.append(
                {
                    "name": cat.name,
                    "position": cat.position,
                    "channels": chnls,
                    "overwrites": role_ovs,
                }
            )

        categories = sorted(categories, key=lambda x: x["position"])
        guild_save["categories"] = categories

        guild_save = json.dumps(guild_save, indent=4)

        uuid_current = await Database.save_guild(
            guild.id, interaction.user.id, guild_save, guild.name, note
        )

        await interaction.response.send_message(f"Guild saved as `{uuid_current}.json`")

    @app_commands.command(
        name="load_server",
        description="Load a saved server (deletes everything, then pastes the saved server)))",
    )
    @app_commands.guild_only()
    @app_commands.describe(uuid="The uuid of the save")
    @is_guild_owner()
    @bot_has_permissions(administrator=True)
    async def load_server(self, interaction: discord.Interaction, uuid: str):
        uuid = uuid.removesuffix(".json")

        try:
            guild_save = await Database.load_guild(uuid, interaction.user.id)

            guild_save = json.loads(guild_save)
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description=e), ephemeral=True
            )
            return

        guild = interaction.guild
        await interaction.response.defer()

        channels = await guild.fetch_channels()
        roles = await guild.fetch_roles()

        # delete all channels and all roles
        for channel in channels:
            try:
                await channel.delete()
            except Exception:
                pass

        for role in roles:
            # check if bot role is above role we want to delete
            if not role.managed and not role.is_default() and role < guild.me.top_role:
                try:
                    await role.delete()
                except Exception:
                    pass

        roles_map = {}

        # create roles
        for role in guild_save["roles"]:
            if role["name"] == "🉥":
                roles_map[role["id"]] = guild.default_role.id
                continue

            new_role = await guild.create_role(
                name=role["name"],
                color=discord.Color(role["color"]),
                mentionable=role["mentionable"],
                hoist=role["hoist"],
                permissions=discord.Permissions(role["permissions"]),
            )
            roles_map[role["id"]] = new_role.id

        # create channels
        for channel in guild_save["channels"]:
            ovrs = {}
            for role in channel["overwrites"]:
                role_obj = guild.get_role(roles_map[int(role)])

                ovrs[role_obj] = discord.PermissionOverwrite.from_pair(
                    discord.Permissions(channel["overwrites"][role]["allow"]),
                    discord.Permissions(channel["overwrites"][role]["deny"]),
                )

            try:
                await create_channel(guild, channel, ovrs)
            except Exception:
                pass

        # create categories
        for cat in guild_save["categories"]:
            ovrs = {}
            for role in cat["overwrites"]:
                role_obj = guild.get_role(roles_map[int(role)])
                ovrs[role_obj] = discord.PermissionOverwrite.from_pair(
                    discord.Permissions(cat["overwrites"][role]["allow"]),
                    discord.Permissions(cat["overwrites"][role]["deny"]),
                )

            category = await guild.create_category(
                name=cat["name"],
                overwrites=(ovrs),
            )

            for channel in cat["channels"]:
                ovrs = {}
                for role in channel["overwrites"]:
                    role_obj = guild.get_role(roles_map[int(role)])
                    ovrs[role_obj] = discord.PermissionOverwrite.from_pair(
                        discord.Permissions(channel["overwrites"][role]["allow"]),
                        discord.Permissions(channel["overwrites"][role]["deny"]),
                    )

                await create_channel(guild, channel, ovrs, category)

        await interaction.user.send("Guild loaded succesfully!")

    @app_commands.command(
        name="list_saved_servers", description="List all your saved servers"
    )
    async def list_saved_servers(self, interaction: discord.Interaction):
        guilds = await Database.get_saves(interaction.user.id)

        if not guilds:
            await interaction.response.send_message(
                embed=Embed("", color=0x880000, description="No guilds saved")
            )
            return

        embed = Embed("Guilds saved", color=0x00FF00)

        for guild in guilds:
            embed.add_field(
                name=f"{guild['guild_name']} ({guild['id']})",
                value=f"Notes: {guild['notes']}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="assign_role_to_all_members", description="Assign a role to every member"
    )
    @app_commands.guild_only()
    @app_commands.describe(role="The role to give everyone")
    @bot_has_permissions(administrator=True)
    @user_has_permissions(administrator=True)
    async def assign_role_to_all_members(
        self, interaction: discord.Interaction, role: discord.Role
    ):
        guild = interaction.guild

        # send normal message

        for index, member in enumerate(guild.members):
            if role not in member.roles:
                await member.add_roles(role)

            if index % 100 == 0 and index != 0:
                percent = round((index / len(guild.members)) * 100, 2)

                await interaction.edit_original_response(content=f"{percent}% done")

        await interaction.edit_original_response(content="100\% done")
