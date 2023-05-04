import time
import openai
import asyncio
import discord
import pydash as _

from discord import app_commands
from discord.ext import commands

from botya import __version__, OPENAI_API_KEY
from botya import premium_ent
from botya.config import BUY_PREMIUM_LINK, DISOCRD_SERVER_LINK
from botya.core.utils.embed import Embed
from botya.core.db.db import Database
from botya.core.utils.checks import is_premium
from botya.core.utils.types import tz
from botya.core.utils.views import (
    BuyPremiumView,
    BuyPremiumButton,
    NewGPTConversationView,
    NewGPTConversationButton,
    AuthorButton,
)

from datetime import datetime
from pydash import py_
from currency_converter import CurrencyConverter

from .helpers import Currency


openai.api_key = OPENAI_API_KEY


def gpt_request(messages):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        max_tokens=1000,
        messages=messages,
    )


class User(commands.Cog, name="User", description="for everyone"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's response time ")
    async def ping(self, interaction: discord.Interaction):
        ping = int(self.bot.latency * 1000)

        if ping < 75:
            text = "🟢 Excellent"
        elif ping < 200:
            text = "🟢 Good"
        elif ping < 350:
            text = "🟡 Alright"
        elif ping < 600:
            text = "🔴 Bad"
        else:
            text = "⚫ Terrible"

        embed = Embed(
            title="🏓 Latency",
            description=f"{text}\n```\n{ping}ms\n```",
            footer=[
                "If the bot feels fast, don't worry about high numbers\nScale: Excellent | Good | Alright | Bad | Terrible",
                "",
            ],
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Help! I need somebody!")
    @app_commands.describe(
        cog_or_command="Cog or command you want to get specific information about"
    )
    async def help(self, interaction: discord.Interaction, cog_or_command: str = None):
        prefix = "/"
        version = __version__
        discord_link = f"**{DISOCRD_SERVER_LINK}**"

        owner = 288717325765443587
        owner_name = "Memetelve#3377"

        if not cog_or_command:
            try:
                owner = interaction.guild.get_member(owner).mention
            except AttributeError:
                owner = owner_name

            embed = discord.Embed(
                title="Commands and modules",
                color=discord.Color.blue(),
                description="Use `/help <module>` to gain more information about that module",
            )

            app_coms = await self.bot.tree.fetch_commands()

            for cog in enumerate(self.bot.cogs):
                cog_ob = self.bot.cogs[cog[1]]

                if getattr(cog_ob, "hidden", False):
                    continue

                commands = ""
                for com in cog_ob.get_app_commands():
                    if len(commands) > 950:
                        embed.add_field(
                            name=f"{cog[1]} - {cog_ob.description}",
                            value=commands,
                            inline=False,
                        )
                        commands = ""

                    if com.name in [comm.name for comm in app_coms]:
                        for cmd in app_coms:
                            if cmd.name == com.name:
                                commands += f"{cmd.mention} - `{cmd.description}`\n"
                                break
                    else:
                        commands += f"`{com.name}` - {com.description}\n"

                doc = self.bot.cogs[cog[1]].description

                embed.add_field(name=f"{cog[1]} - {doc}", value=commands, inline=False)

            embed.add_field(
                name="About",
                value=f"The Bots is developed by {owner}\n\
                                    Please visit {discord_link} to receive support, submit ideas or bugs.",
            )
            embed.set_footer(text=f"Bot is running {version}")

        elif cog := self.bot.get_cog(cog_or_command):
            embed = discord.Embed(
                title=f"{cog_or_command} - {cog.description}",
                color=discord.Color.blue(),
            )
            for com in cog.get_app_commands():
                embed.add_field(
                    name=f"`{prefix}{com.name}`", value=com.description, inline=False
                )
        elif com := self.bot.tree.get_command(cog_or_command):
            # check if com is a discord.app_commands.commands.Group
            if isinstance(com, discord.app_commands.commands.Group):
                embed = discord.Embed(
                    title=f"{com.name} - {com.description}", color=discord.Color.blue()
                )
                for sub_com in com.commands:
                    embed.add_field(
                        name=f"`{prefix}{sub_com.name}`",
                        value=sub_com.description,
                        inline=False,
                    )
            else:
                params = "".join(
                    f"<{param.name}: {str(param.type)[21:]}> "
                    for param in com.parameters
                )

                embed = discord.Embed(
                    title=f"`{prefix}{com.name}`",
                    description=com.description,
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name="Usage", value=f"`{prefix}{com.name} {params}`", inline=False
                )
                embed.add_field(
                    name="Parameters",
                    value="\n".join(
                        f"`<{param.name}>` - {param.description}"
                        for param in com.parameters
                    ),
                    inline=False,
                )
        else:
            embed = discord.Embed(title="Error", color=discord.Color.red())
            embed.add_field(
                name="Command or module not found",
                value=f"`{cog_or_command}`",
                inline=False,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="find", description="Give an ID and i will try to find what it is"
    )
    @app_commands.describe(id="ID of the object you want to find")
    async def find(self, interaction: discord.Interaction, id: str):
        # convert id to int
        try:
            id = int(id)
        except ValueError:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Error", description="Invalid ID", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        # try to fetch user
        try:
            user = await self.bot.fetch_user(id)
            return await interaction.response.send_message(
                embed=Embed(description=f"User: {user.mention}")
            )
        except Exception:
            pass

        # try to fetch channel
        try:
            channel = await self.bot.fetch_channel(id)
            return await interaction.response.send_message(
                embed=Embed(
                    description=f"Channel: {channel.mention}\nGuild: {channel.guild.name}"
                )
            )
        except Exception:
            pass

        # try to fetch guild
        try:
            guild = await self.bot.fetch_guild(id, with_counts=True)
            return await interaction.response.send_message(
                embed=Embed(
                    description=f"Guild: {guild.name}\nOnline: {guild.approximate_presence_count}/{guild.approximate_member_count}"
                )
            )
        except Exception:
            pass

        # try to fetch role
        try:
            role = await interaction.guild.fetch_role(id)
            return await interaction.response.send_message(
                embed=Embed(description=f"Role: {role.mention}")
            )
        except Exception:
            pass

        # try to fetch emoji
        try:
            emoji = await interaction.guild.fetch_emoji(id)
            return await interaction.response.send_message(
                embed=Embed(description=f"Emoji: {emoji}")
            )
        except Exception:
            pass

        # embed nothing with this id found using Embed
        embed = Embed(
            title="Error",
            color=discord.Color.red(),
            description="Nothing with this ID found",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invite_info", description="Get info about invite")
    @app_commands.describe(member="Invite code")
    @app_commands.guild_only()
    async def invite_info(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        try:
            embed = Embed(description="Getting user info...")
            await interaction.response.defer(thinking=True)

            start = time.time()

            invites = await Database.get_invites(member.guild.id, member.id)

            real, fake, left = 0, 0, 0

            for invite in invites:
                status = invite["status"]
                if status == 0:
                    real += 1
                elif status == 1:
                    left += 1
                elif status == 2:
                    fake += 1

            end = time.time()

            embed = Embed(
                description=f"Invite stats for user {member.mention} generated in {int(round((end - start)*1000, 0))}ms\n\n✅Total: {real+fake+left}\n❌Fake: {fake}\n🚪Left: {left}",
                fields=[
                    [
                        "Real invites",
                        f"This user has currently *{real}*  🪴real invites.",
                        False,
                    ]
                ],
                footer=[f"{self.bot.user.name} • invoked by {interaction.user}", ""],
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(e)

    @app_commands.command(name="convert_currency", description="Convert currency")
    @app_commands.describe(
        amount="Amount of currency to convert",
        from_currency="Currency to convert from",
        to_currency="Currency to convert to",
    )
    async def convert_currency(
        self,
        interaction: discord.Interaction,
        amount: float,
        from_currency: Currency,
        to_currency: Currency,
    ):
        from_currency = from_currency.value
        to_currency = to_currency.value

        c = CurrencyConverter()
        converted_amount = c.convert(amount, from_currency, to_currency)

        embed = Embed(
            title=f"{amount:.2f} {from_currency} is {converted_amount:.2f} {to_currency}",
            color=0x00,
            footer=[
                f"Exchange rate as of {datetime.now():%d %B %Y %H:%M:%S} UTC",
                "",
            ],
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="server", description="Displays information about the current server."
    )
    @app_commands.guild_only()
    async def server(self, interaction: discord.Interaction):
        # Get the guild object for the current server
        guild = interaction.guild

        # Create an embed to display server information
        embed = Embed(title=guild.name, color=discord.Color.green())
        embed.add_field(name="Owner", value=guild.owner.name)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.set_thumbnail(url=guild.icon.url)

        # Send the embed as a response to the interaction
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ask_gpt", description="Ask GPT-3.5-turbo a question")
    @app_commands.describe(question="Question to ask GPT-3.5-turbo")
    @is_premium()
    async def ask_gpt(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer(thinking=True)

        timer_start = time.time() * 1000

        past_messages = await Database.get_gpt_conversation(interaction.user.id)
        past_tokens = past_messages[0]["tokens"]

        all_messages = _.flatten(
            [
                x["conversation"]
                for x in await Database.get_gpt_conversations_by_user(
                    interaction.user.id
                )
            ]
        )
        all_messages = _.filter_(all_messages, lambda x: x["role"] != "system")

        # get first day of this month
        today = datetime.today()
        first_day_of_month = today.replace(day=1)

        if past_tokens > 3090:
            return await interaction.followup.send(
                embed=Embed(
                    title="Error",
                    color=discord.Color.red(),
                    description="Your conversation is too long. Please start a new conversation.",
                ),
                ephemeral=True,
            )

        past_messages = past_messages[0]["conversation"][1:]
        x = _.filter_(
            all_messages,
            lambda x: datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M:%S")
            >= first_day_of_month,
        )

        tokens_used_this_month = _.sum_by(x, lambda x: x["tokens"])

        if tokens_used_this_month > 1_000_000:
            return await interaction.followup.send(
                embed=Embed(
                    title="Error",
                    color=discord.Color.red(),
                    description="You have reached your monthly limit of 1,000,000 tokens. Please wait until the next month to continue your conversation.",
                ),
                ephemeral=True,
            )
        messages_dict = [
            {
                "role": "system",
                "content": "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible.\nKnowledge cutoff: 2021-09-01\nCurrent date: 2023-03-02",
            },
        ]
        messages_dict += past_messages
        messages_dict.append(
            {
                "role": "user",
                "content": question,
            }
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            gpt_request,
            py_(messages_dict)
            .map(lambda obj: _.omit(obj, "tokens", "datetime"))
            .value(),
        )

        messages_dict[-1]["tokens"] = response["usage"]["prompt_tokens"]
        messages_dict[-1]["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messages_dict.append(response.choices[0].message)
        messages_dict[-1]["tokens"] = response["usage"]["completion_tokens"]
        messages_dict[-1]["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        timer_end = time.time() * 1000

        embed = Embed(
            title="ChatGPT response",
            color=0x119C7A,
            description=f"```{response.choices[0].message.content}```"
            if "```" not in response.choices[0].message.content
            else response.choices[0].message.content,
            author=[
                "ChatGPT",
                "https://static.vecteezy.com/system/resources/previews/021/608/790/original/chatgpt-logo-chat-gpt-icon-on-black-background-free-vector.jpg",
            ],
            footer=[f"Response time: {(timer_end-timer_start):.0f}ms", ""],
        )

        view = NewGPTConversationView()
        view.add_item(
            NewGPTConversationButton(
                style=discord.ButtonStyle.blurple, label="Reset conversation", emoji="🧹"
            )
        )
        view.add_item(
            AuthorButton(
                style=discord.ButtonStyle.gray,
                label=f"{interaction.user}",
            )
        )

        await interaction.followup.send(embed=embed, view=view)

        await Database.edit_gpt_conversation(
            interaction.user.id,
            messages_dict,
            past_tokens + response["usage"]["total_tokens"],
        )

    @app_commands.command(name="premium", description="Check if you are premium")
    async def premium(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        x = False

        if ent := premium_ent.get(interaction.user.id) or premium_ent.get(
            interaction.guild.id
        ):
            if ent["premium_until"] > datetime.now(tz=tz):
                x = True

        if x:
            until = ent["premium_until"]
            discord_timestamp = time.mktime(until.timetuple())
            until = [["Premium until:", f"<t:{int(discord_timestamp)}:f>"]]
        else:
            until = None

        embed = Embed(
            "Premium status",
            color=0x119C7A if x else 0x9C1A1A,
            description=f"You are {'' if x else '**not**'} premium {'✅' if x else '❌'}",
            fields=until,
        )

        view = BuyPremiumView()
        view.add_item(
            BuyPremiumButton(
                label="Buy premium",
                style=discord.ButtonStyle.url,
                url=BUY_PREMIUM_LINK,
            )
        )

        await interaction.followup.send(
            embed=embed,
            view=view,
        )
