import discord
import datetime
import pytz


def check_if_none(text):
    if text in [False, True]:
        return text
    elif text is None:
        return ""
    temp = text.strip()
    temp = temp.lower()
    return "" if temp == "none" else text


def Embed(
    title=None,
    color=0x2F3136,
    url=None,
    description=None,
    fields=None,
    author=None,
    thumbnail=None,
    footer=None,
    image=None,
    timestamp: bool = False,
    timezone=None,
):

    embed = discord.Embed(title=title, color=color, url=url, description=description)

    if fields:
        for field in fields:
            if len(field[1]) < 1:
                field[1] = "` `"
            try:
                inline = field[2]
            except Exception:
                inline = False
            embed.add_field(name=field[0], value=field[1], inline=inline)

    if author is not None:
        embed.set_author(name=author[0], icon_url=author[1])
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)
    if footer is not None:
        embed.set_footer(text=footer[0], icon_url=footer[1])
    if image is not None:
        embed.set_image(url=image)
    if timestamp:
        if timezone is not None:

            zone = pytz.timezone(timezone)
            embed.timestamp = datetime.datetime.now(zone)
        else:
            embed.timestamp = datetime.datetime.now()

    return embed
