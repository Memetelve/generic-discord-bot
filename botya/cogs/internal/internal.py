import os
import time
import json
import discord
import traceback
import inspect
import rich
import re as r

from aioconsole import ainput
from urllib.request import urlopen
from discord.ext import commands
from datetime import datetime


from rich import box
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table


from botya import __version__
from botya import premium_ent
from botya.config import OWNER_ID
from botya.core.db.db import Database
from botya.core.utils.types import tz
from botya.core.utils.embed import Embed

from botya.cache import _cache


async def get_ip():
    d = str(urlopen("http://checkip.dyndns.com/").read())

    print(r.compile(r"Address: (\d+\.\d+\.\d+\.\d+)").search(d).group(1))


async def create_embed():
    # https://glitchii.github.io/embedbuilder

    try:
        with open("./botya/cogs/owner/embed.json", "r", encoding="utf-8") as fh:
            message = json.loads(fh.read())
        # text before embed
        content = message["content"] if "content" in message else ""

        message = message["embeds"][0]

        # embed variables
        title = message["title"] if "title" in message else ""
        description = message["description"] if "description" in message else ""
        color = message["color"] if "color" in message else 50918
        timestamp = message["timestamp"] if "timestamp" in message else None
        url = message["url"] if "url" in message else ""

        if timestamp:
            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=timestamp,
            url=url,
        )

        # author
        if "author" in message:
            author_name = (
                message["author"]["name"] if "name" in message["author"] else ""
            )
            author_icon = (
                message["author"]["icon_url"] if "icon_url" in message["author"] else ""
            )
            author_url = message["author"]["url"] if "url" in message["author"] else ""
        else:
            author_name = ""
            author_icon = ""
            author_url = ""
        # thumbnail
        if "thumbnail" in message:
            thumbnail_url = (
                message["thumbnail"]["url"] if "url" in message["thumbnail"] else ""
            )
        else:
            thumbnail_url = ""
        # image
        if "image" in message:
            image_url = message["image"]["url"] if "url" in message["image"] else ""
        else:
            image_url = ""
        # footer
        if "footer" in message:
            footer_text = (
                message["footer"]["text"] if "text" in message["footer"] else ""
            )
            footer_icon = (
                message["footer"]["icon_url"] if "icon_url" in message["footer"] else ""
            )
        else:
            footer_text = ""
            footer_icon = ""

        embed.set_author(name=author_name, icon_url=author_icon, url=author_url)
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_image(url=image_url)
        embed.set_footer(text=footer_text, icon_url=footer_icon)

        if "fields" in message:
            for field in message["fields"]:
                name = field["name"] if "name" in field else ""
                value = field["value"] if "value" in field else ""
                inline = field["inline"] if "inline" in field else False

                inline = str(inline) == "true"
                embed.add_field(name=name, value=value, inline=inline)

        return embed, content

    except Exception as e:
        print(e)
        return None, None


async def handle_exit(bot):
    await bot.close()


async def handle_show_ip():
    print(get_ip())


async def handle_check_premium(ent_id: int):
    ent_id = int(ent_id)
    ent = premium_ent.get(ent_id)
    if not ent:
        print(f"{ent_id} is not premium.")
        return

    if ent["premium_until"] > datetime.now(tz=tz):
        date = ent["premium_until"].strftime("%d/%m/%Y %H:%M:%S")
        print(f"{ent_id} is premium until {date}.")
    else:
        print(f"{ent_id} is not premium.")


async def handle_show_cache():
    print(_cache)


async def handle_clear(bot):
    # For Window
    if os.name == "nt":  # 'nt' stands for Windows
        os.system("cls")
    else:
        os.system("clear")

    INTRO = """
██████╗  ██████╗ ████████╗██╗   ██╗ █████╗
██╔══██╗██╔═══██╗╚══██╔══╝╚██╗ ██╔╝██╔══██╗
██████╔╝██║   ██║   ██║    ╚████╔╝ ███████║
██╔══██╗██║   ██║   ██║     ╚██╔╝  ██╔══██║
██████╔╝╚██████╔╝   ██║      ██║   ██║  ██║
╚═════╝  ╚═════╝    ╚═╝      ╚═╝   ╚═╝  ╚═╝
"""
    table_general_info = Table(show_edge=False, show_header=False, box=box.ROUNDED)
    table_general_info.add_row("Prefixes", ", ".join(bot.command_prefix))
    table_general_info.add_row("Language", "English")
    table_general_info.add_row("Botya version", __version__)
    table_general_info.add_row("discord.py version", discord.__version__)
    table_general_info.add_row("Storage type", "SupaBase")

    guilds = len(bot.guilds)
    users = len(set(list(bot.get_all_members())))

    table_counts = Table(show_edge=False, show_header=False, box=box.MINIMAL)
    # String conversion is needed as Rich doesn't deal with ints
    table_counts.add_row("Shards", str(bot.shard_count))
    table_counts.add_row("Servers", str(guilds))
    if bot.intents.members:  # Lets avoid 0 Unique Users
        table_counts.add_row("Unique Users", str(users))
    table_counts.add_row("")
    table_counts.add_row("Cogs", str(len(bot.cogs)))

    commands_count = 0
    for command in bot.tree.walk_commands():
        commands_count += 1

    table_counts.add_row("Commands", str(commands_count))

    rich_console = rich.get_console()
    rich_console.print(INTRO, style="cyan", markup=False, highlight=False)
    rich_console.print(
        Columns(
            [
                Panel(table_general_info, title=str(bot.user.name)),
                Panel(table_counts),
            ],
            equal=True,
            align="center",
        )
    )


async def handle_set_premium(
    owner, ent_id: int, premium_type: str, tier: int, year: int, month: int, day: int
):
    ent_id, tier, year, month, day = (
        int(ent_id),
        int(tier),
        int(year),
        int(month),
        int(day),
    )

    timestamptz = datetime(year, month, day, tzinfo=tz)

    assert await Database.set_premium(
        ent_id, timestamptz.isoformat(), premium_type, tier
    )

    discord_timestamp = time.mktime(timestamptz.timetuple())

    premium_ent[ent_id] = {
        "premium_tier": tier,
        "premium_until": timestamptz,
        "premium_type": premium_type,
    }

    embed = Embed(
        description=f"Set premium for `{ent_id}`",
        color=0x000,
        fields=[
            ["Until", f"<t:{int(discord_timestamp)}:f>"],
            ["Type:", str(premium_type)],
            ["Tier:", str(tier)],
        ],
    )

    await owner.send(embed=embed)


async def handle_show_guilds(bot, owner):
    desc = ""
    async for guild in bot.fetch_guilds(limit=150):
        desc += f"{guild.name} (`{guild.id}`) {guild.owner}\n"
    await owner.send(embed=Embed(description=desc))


async def handle_check_gpt_usage(user_id):
    data = await Database.get_gpt_conversations_by_user(user_id)

    tokens = sum([conv["tokens"] for conv in data])
    price = 0.002 * tokens / 1000

    print(f"{user_id} has used {tokens} tokens -> ${price}")


async def handle_help(commands):
    desc = ""
    for command, args in commands.items():
        args = inspect.getfullargspec(commands[command][0])[0]
        arg_types = inspect.getfullargspec(commands[command][0])[6]
        args = args[len(commands[command][1]) :]

        comm_desc = ""
        for arg in args:
            arg_type = arg_types.get(arg, "UNK")
            if arg_type != "UNK":
                arg_type = arg_type.__name__

            comm_desc += f"<{arg}: {arg_type}> "

        comm_desc = comm_desc.strip()
        comm_desc = comm_desc.replace("  ", " ")

        desc += f"    {command} {comm_desc}\n"

    print(f"{desc}")


class Internal(commands.Cog, name="", description=""):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hidden = True

    @commands.Cog.listener()
    async def on_ready(self):
        owner = self.bot.get_user(OWNER_ID)

        commands = {
            "exit": [handle_exit, [self.bot]],
            "show_ip": [get_ip, []],
            "check_premium": [handle_check_premium, []],
            "show_cache": [handle_show_cache, []],
            "set_premium": [handle_set_premium, [owner]],
            "show_guilds": [handle_show_guilds, [self.bot, owner]],
            "check_gpt_usage": [handle_check_gpt_usage, []],
            "clear": [handle_clear, [self.bot]],
        }

        commands["help"] = [handle_help, [commands]]

        while True:
            command_input = await ainput("Botya > ")
            command_input = command_input.split()
            command, args = command_input[0], command_input[1:]

            try:
                if command in commands:
                    await Database.add_admin_log(" /|\\".join(command_input))
                    await commands[command][0](*commands[command][1], *args)

                else:
                    print("Invalid command")

            except TypeError as e:
                print(e)

                args = inspect.getfullargspec(commands[command][0])[0]
                arg_types = inspect.getfullargspec(commands[command][0])[6]
                args = args[len(commands[command][1]) :]

                desc = ""
                for arg in args:
                    arg_type = arg_types.get(arg, "UNK")
                    if arg_type != "UNK":
                        arg_type = arg_type.__name__

                    desc += f"<{arg}: {arg_type}> "

                desc = desc.strip()
                desc = desc.replace("  ", " ")

                print(f"Usage: {command} {desc}")

            except Exception:
                traceback.print_exc()
