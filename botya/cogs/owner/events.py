import rich
import discord
import aiohttp
import io

from discord.ext import commands

from botya import __version__
from botya.cache import _cache

from rich import box
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table


console = Console()


class OwnerEvents(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id in [905528879312150608, 887996304842715176]:
            return

        urls = []

        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                url = attachment.url  # must be an image
                async with aiohttp.ClientSession() as session:  # creates session
                    async with session.get(url) as resp:  # gets image from url
                        img = await resp.read()  # reads image from response
                        with io.BytesIO(img) as file:  # converts to file-like object
                            if message.guild:
                                filename = (
                                    f"guild-{message.guild.id}-{message.channel.id}.png"
                                )
                            else:
                                filename = f"dm-{message.author.id}.png"

                            image = await self.archive_1.send(
                                file=discord.File(file, filename=filename)
                            )
                            urls.append(image.attachments[0].url)

        if urls:
            _cache[message.id] = urls

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self.bot.get_channel(1044330481619046441)

        await channel.send(f"Joined {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_ready(self):
        self.archive_1 = self.bot.get_channel(1094007339822092362)

        # sourcery skip: for-index-underscore, sum-comprehension
        # clearConsole()
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="Slash commands"
            )
        )
        INTRO = """
██████╗  ██████╗ ████████╗██╗   ██╗ █████╗
██╔══██╗██╔═══██╗╚══██╔══╝╚██╗ ██╔╝██╔══██╗
██████╔╝██║   ██║   ██║    ╚████╔╝ ███████║
██╔══██╗██║   ██║   ██║     ╚██╔╝  ██╔══██║
██████╔╝╚██████╔╝   ██║      ██║   ██║  ██║
╚═════╝  ╚═════╝    ╚═╝      ╚═╝   ╚═╝  ╚═╝
"""
        table_general_info = Table(
            show_edge=False, show_header=False, box=rich.box.ROUNDED
        )
        table_general_info.add_row("Prefixes", ", ".join(self.bot.command_prefix))
        table_general_info.add_row("Language", "English")
        table_general_info.add_row("Botya version", __version__)
        table_general_info.add_row("discord.py version", discord.__version__)
        table_general_info.add_row("Storage type", "SupaBase")

        guilds = len(self.bot.guilds)
        users = len(set(list(self.bot.get_all_members())))

        table_counts = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        # String conversion is needed as Rich doesn't deal with ints
        table_counts.add_row("Shards", str(self.bot.shard_count))
        table_counts.add_row("Servers", str(guilds))
        if self.bot.intents.members:  # Lets avoid 0 Unique Users
            table_counts.add_row("Unique Users", str(users))
        table_counts.add_row("")
        table_counts.add_row("Cogs", str(len(self.bot.cogs)))

        commands_count = 0
        for command in self.bot.tree.walk_commands():
            commands_count += 1

        table_counts.add_row("Commands", str(commands_count))

        rich_console = rich.get_console()
        rich_console.print(INTRO, style="cyan", markup=False, highlight=False)
        rich_console.print(
            Columns(
                [
                    Panel(table_general_info, title=str(self.bot.user.name)),
                    Panel(table_counts),
                ],
                equal=True,
                align="center",
            )
        )
