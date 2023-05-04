import discord
import requests
import asyncio

from discord.ext import commands, tasks


#
# btw this is def not working
#
class OwnerTasks(commands.Cog):
    @tasks.loop(seconds=60 * 10 - 10)
    async def current_war_coc(self):
        await asyncio.sleep(5)

        token = "trolololo"
        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}

        endpoint = "https://api.clashofclans.com/v1/clans/%232YGG2CC88/currentwar"

        response = requests.get(endpoint, headers=headers).json()

        try:
            state = response["state"]
        except Exception:
            return

        with open("state.txt", "w+") as f:
            line = f.read()

            if state in line:
                return
            elif state == "warEnded":
                f.write(state)
            else:
                f.write(state)
                return

        enemy_clan_name = response["opponent"]["name"]

        clan_stars = response["clan"]["stars"]
        enemy_clan_stars = response["opponent"]["stars"]

        if clan_stars > enemy_clan_stars:
            status = "wygraną"
        elif clan_stars < enemy_clan_stars:
            status = "przegraną"
        else:
            status = "remisem"

        embed = discord.Embed(
            title=f"Wojna przeciw {enemy_clan_name} zakończona **{status}**"
        )

        embed.set_thumbnail(url=response["opponent"]["badgeUrls"]["medium"])

        members = response["clan"]["members"]
        opponents = response["opponent"]["members"]

        fields = []

        for member in members:
            mem_pos = member["mapPosition"]
            mem_name = member["name"]

            try:
                desc = ""

                for i, attack in enumerate(member["attacks"]):
                    for opp in opponents:
                        if opp["tag"] == attack["defenderTag"]:
                            position = opp["mapPosition"]
                            opp_name = opp["name"]
                            break

                    stars = attack["stars"]
                    order = attack["order"]

                    prev_stars = 0

                    for mm in members:
                        try:
                            for atk in mm["attacks"]:
                                if (
                                    atk["order"] >= order
                                    or attack["defenderTag"] != atk["defenderTag"]
                                ):
                                    pass
                                elif atk["stars"] > prev_stars:
                                    prev_stars = atk["stars"]
                        except KeyError:
                            pass

                    if stars - prev_stars < 0:
                        stars = ""
                    else:
                        stars = (stars - prev_stars) * "⭐"

                    if i == 0:
                        atk_no = 1
                    else:
                        atk_no = 2

                    desc += f"Atak {atk_no}: `{position}. {opp_name}` {stars}\n"

            except KeyError:
                pass

            if desc == "":
                desc = "Brak ataków"

            fields.append([mem_pos, mem_name, desc])

        fields = sorted(fields, key=lambda x: x[0], reverse=False)
        for field in fields:
            embed.add_field(
                name=f"{field[0]}. {field[1]}", value=field[2], inline=False
            )

        guild = self.bot.get_guild(1018957340243923066)
        channel = guild.get_channel(1018957341112139878)

        await channel.send(embed=embed)
