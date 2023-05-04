import discord
from discord import ui

from botya.core.utils.embed import Embed
from botya.core.db.db import Database


class DeleteConfirmModal(
    discord.ui.Modal, title="Are you sure? You can't undo this action."
):
    name = discord.ui.TextInput(
        label='Type "DELETE" to confirm',
        placeholder="DELETE?",
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")


class BuyPremiumView(ui.View):
    def __init__(self, custom_id="BuyPremiumView", *args, **kwargs):
        super().__init__(timeout=None)
        self.custom_id = custom_id


class BuyPremiumButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DefaultRoleView(ui.View):
    def __init__(self, custom_id="ReactionRoleView", *args, **kwargs):
        super().__init__(timeout=None)
        self.custom_id = custom_id


class DefaultRoleButton(discord.ui.Button):
    def __init__(self, custom_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        role = interaction.guild.get_role(int(self.custom_id))
        if role is None:
            return

        target = interaction.user

        try:
            if role not in target.roles:
                await target.add_roles(role)
                embed = Embed(description=f"✅ Added {role.mention}", color=0x4EBA52)
            else:
                await target.remove_roles(role)
                embed = Embed(description=f"❌ Removed {role.mention}", color=0xB12020)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(e)


class TicketMessageView(ui.View):
    def __init__(self, custom_id="TicketMessageView", *args, **kwargs):
        super().__init__(timeout=None)
        self.custom_id = custom_id


class TicketOpenButton(discord.ui.Button):
    def __init__(self, custom_id="TicketOpenButton", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # get channel topic and get user id from it. Then get user
        channel = interaction.channel

        # get open category from database
        open_tickets_category_id = await Database.get_open_tickets_category_id(
            interaction.guild.id
        )
        open_tickets_category = interaction.guild.get_channel(open_tickets_category_id)

        # move channel to open category
        await channel.edit(category=open_tickets_category)

        # edit view
        ticket_message_view = TicketMessageView()
        ticket_message_view.add_item(
            TicketCloseButton(
                label="Close ticket", style=discord.ButtonStyle.red, emoji="🔒"
            )
        )

        await interaction.message.edit(view=ticket_message_view)

        try:
            embed = Embed(
                description=f"✅ Ticket Re-Opened by {interaction.user.mention}",
                color=0x4EBA52,
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(e)


class TicketCloseButton(discord.ui.Button):
    def __init__(self, custom_id="TicketCloseButton", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # get closed tickets category id from database
        closed_tickets_category_id = await Database.get_closed_tickets_category_id(
            interaction.guild.id
        )
        closed_tickets_category = interaction.guild.get_channel(
            closed_tickets_category_id
        )

        # get the interaction message
        message = await interaction.channel.fetch_message(interaction.message.id)

        # create new view and make this button disabled
        view = TicketMessageView()
        view.add_item(
            TicketCloseButton(
                label="Closed", disabled=True, style=discord.ButtonStyle.red, emoji="🔒"
            )
        )
        view.add_item(
            TicketOpenButton(
                label="Re-Open", style=discord.ButtonStyle.green, emoji="🔓"
            )
        )
        view.add_item(
            TicketDeleteButton(
                label="Delete", style=discord.ButtonStyle.red, emoji="🗑️"
            )
        )

        # move channel to this category and teke away permissions from user
        await interaction.channel.edit(category=closed_tickets_category)
        await interaction.channel.set_permissions(
            interaction.user,
            read_messages=False,
            send_messages=False,
            view_channel=False,
        )

        # edit the message
        await message.edit(view=view)

        # create string with current timedate (ex. 19:52:00 12/12/2021)
        datetime = interaction.created_at.strftime("%H:%M:%S %d/%m/%Y")

        # send message to user
        embed = Embed(
            description=f"<:goldkey:1041829600830947339> Ticket closed by **{interaction.user.name}**",
            color=0xB12020,
            footer=[f"Ticket ID: {interaction.channel.id}", ""],
            author=[
                f"{interaction.guild.name} - {datetime}",
                getattr(interaction.guild.icon, "url", ""),
            ],
        )

        await interaction.user.send(embed=embed)

        # send message in channel with info who closed the ticket
        embed = Embed(
            description=f"<:goldkey:1041829600830947339> Ticket closed by {interaction.user.mention}",
            color=0xB12020,
        )
        await interaction.channel.send(embed=embed)


class TicketView(ui.View):
    def __init__(self, custom_id="TicketView", *args, **kwargs):
        super().__init__(timeout=None)
        self.custom_id = custom_id


class TicketButton(discord.ui.Button):
    def __init__(self, custom_id="TicketButton", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # check if user has a open ticket, if not create a new one for them
        # create it in open tickets category and send a message with the ticket id
        # get open tickets category id from database

        open_tickets_category_id = await Database.get_open_tickets_category_id(
            interaction.guild.id
        )
        open_tickets_category = interaction.guild.get_channel(open_tickets_category_id)

        for channel in open_tickets_category.channels:
            if channel.topic == str(interaction.user.id):
                embed = Embed(
                    description=f"You already have an open ticket in {channel.mention}",
                    color=0xB12020,
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        # get ticket count from database
        ticket_count = await Database.get_ticket_count(interaction.guild.id)
        ticket_count = "{:0>4}".format(ticket_count)

        # create new ticket
        ovr = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False, view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, view_channel=True
            ),
        }

        new_ticket = await open_tickets_category.create_text_channel(
            name=f"ticket-{ticket_count}",
            topic=str(interaction.user.id),
            overwrites=ovr,
        )

        # create view
        ticket_message_view = TicketMessageView()
        ticket_message_view.add_item(
            TicketCloseButton(
                label="Close ticket", style=discord.ButtonStyle.red, emoji="🔒"
            )
        )

        # create ticket message
        embed = Embed(
            description="Support will be with you shortly.\nTo close this ticket react with 🔒",
            color=0x4EBA52,
        )
        await new_ticket.send(
            f"{interaction.user.mention}", embed=embed, view=ticket_message_view
        )

        embed = Embed(
            description=f"✅ Created a new ticket in {new_ticket.mention}",
            color=0x4EBA52,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # update ticket count in database
        await Database.update_ticket_count(interaction.guild.id)


class TicketDeleteButton(discord.ui.Button):
    def __init__(self, custom_id="TicketDeleteButton", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.channel.delete()


class NewGPTConversationView(discord.ui.View):
    def __init__(self, custom_id="NewGPTConversationView", *args, **kwargs):
        super().__init__(timeout=None)
        self.custom_id = custom_id


class NewGPTConversationButton(discord.ui.Button):
    def __init__(self, custom_id="NewGPTConversationButton", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user) != interaction.message.components[0].children[1].label:
            await interaction.response.send_message(
                "This is not your conversation :(", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        await Database.render_gpt_conversation_inactive(interaction.user.id)

        embed = Embed(
            description="If you had a active conversation it has been closed",
            color=0x4EBA52,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


class AuthorButton(discord.ui.Button):
    def __init__(self, custom_id="AuthorButton", *args, **kwargs):
        super().__init__(disabled=True, *args, **kwargs)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
