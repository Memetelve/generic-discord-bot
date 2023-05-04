import discord
import asyncio
import requests
import coc
import datetime


from discord.ext import tasks

from botya.core.db.db import Database

token = "eeyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjBjYzI2MGYxLWRmZGUtNDk4NS1hODc0LTM5YjhhYWUxZmZhMCIsImlhdCI6MTY4MDMwMjY5NSwic3ViIjoiZGV2ZWxvcGVyLzM0MGE4MTAzLWUwOGUtNTRiYy1jNzNkLTViNjViNzY1NTkxYyIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjE3OC4yMzUuMTg1LjE5NiIsIjM3LjQ3LjI0Ny4yMzgiLCI4MS4xOTAuNDguNzciXSwidHlwZSI6ImNsaWVudCJ9XX0._skPlY5xjTxPZqqT1MvjXu7dWj1G5vDuW9EwpJ2PCyY-LsyHVaRM5WrxoaVGcw2VVPw3nJ5RMMvoyb5Jed782Q"
headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}


class ClashOfClansTasks:
    @tasks.loop(seconds=60 * 10 - 10)
    async def check_clash_of_clans_wars(self):
        await asyncio.sleep(5)
        guilds = await Database.get_all_wars()

        # {
        #     "guild_id": 790337229532299320,
        #     "member_joined": 1022907593699622923,
        #     "member_joined_active": True,
        #     "member_left": 1022907593699622923,
        #     "member_left_active": True,
        #     "member_banned": 1022907593699622923,
        #     "member_banned_active": True,
        #     "member_unbanned": 1022907593699622923,
        #     "member_unbanned_active": True,
        #     "member_nickname_changed": 1022907593699622923,
        #     "member_nickname_changed_active": True,
        #     "member_received_role": 1022907593699622923,
        #     "member_received_role_active": True,
        #     "member_lost_role": 1022907593699622923,
        #     "member_lost_role_active": True,
        #     "timeout_given_or_removed": 1022907593699622923,
        #     "timeout_given_or_removed_active": True,
        #     "channel_created": 1022907593699622923,
        #     "channel_created_active": True,
        #     "channel_deleted": 1022907593699622923,
        #     "channel_deleted_active": True,
        #     "role_created": 1022907593699622923,
        #     "role_created_active": True,
        #     "role_deleted": 1022907593699622923,
        #     "role_deleted_active": True,
        #     "message_deleted": 1022907593699622923,
        #     "message_deleted_active": True,
        #     "message_edited": 1022907593699622923,
        #     "message_edited_active": True,
        #     "member_joined_voice_channel": 1022907593699622923,
        #     "member_joined_voice_channel_active": True,
        #     "member_left_voice_channel": None,
        #     "member_left_voice_channel_active": True,
        #     "member_switched_voice_channel": 1022907593699622923,
        #     "member_switched_voice_channel_active": True,
        #     "welcome_channel": 1074077398775119882,
        #     "welcome_message": "[inviter] [nl] [inviteCount]",
        #     "welcome_active": True,
        #     "timezone": "Asia/Bangkok",
        #     "tickets_cat1": 1041407284976308296,
        #     "tickets_cat2": 1041407298897186876,
        #     "coc_war_active": True,
        #     "coc_war_channel": 1074077398775119882,
        #     "coc_clan_tag": "2QCCRYJRC",
        #     "last_coc_war_status": None,
        # }

        # States of war in CLW:
        # "warEnded"
        # "inWar"
        # "preparation"
        async with coc.Client() as client:
            try:
                await client.login(
                    "memetelve1@gmail.com", "PEy!jT5*&tHvH@DpxiQde^Uo#SsbJ"
                )
            except coc.invalidcredentials as error:
                exit(error)

            for guild in guilds:
                last_war_start_time = guild["last_coc_war_status"]
                clanTag = guild["coc_clan_tag"]

                war = await client.get_clan_war(clanTag)
                war_stats = (0, None, False)

                if (
                    war.state == "warEnded"
                    and datetime.datetime.strptime(
                        last_war_start_time, "%Y-%m-%d %H:%M:%S"
                    )
                    != war.end_time
                ):
                    await Database.update_last_war_start_time(
                        guild["guild_id"],
                        datetime.datetime.strftime(war.start_time, "%Y-%m-%d %H:%M:%S"),
                    )
                    war_stats = (1, None, False)
                else:
                    try:
                        group = await client.get_league_group("#" + clanTag)
                        async for war in group.get_wars():
                            if (
                                war.clan.tag == ("#" + clanTag)
                                or war.opponent.tag == ("#" + clanTag)
                                and (
                                    datetime.datetime.strptime(
                                        last_war_start_time, "%Y-%m-%d %H:%M:%S"
                                    )
                                    != war.end_time
                                )
                            ):
                                war_stats = (2, war.war_tag[1:], war.clan.is_opponent)
                                await Database.update_last_war_start_time(
                                    guild["guild_id"],
                                    datetime.datetime.strftime(
                                        war.start_time, "%Y-%m-%d %H:%M:%S"
                                    ),
                                )
                    except Exception:
                        war_stats = (0, None)

                if war_stats[0] == 1:
                    endpoint = (
                        f"https://api.clashofclans.com/v1/clans/%{clanTag}/currentwar"
                    )
                elif war_stats[0] == 2:
                    endpoint = (
                        f"https://api.clashofclans.com/v1/clanwarleagues/wars/%{war[1]}"
                    )
                else:
                    continue

                response = await requests.get(endpoint)
                if war_stats[2]:
                    response["clan"], response["opponent"] = (
                        response["opponent"],
                        response["clan"],
                    )

                enemy_clan_name = response["opponent"]["name"]
                clan_stars = response["clan"]["stars"]
                enemy_clan_stars = response["opponent"]["stars"]

                if clan_stars > enemy_clan_stars:
                    status = "win"
                elif clan_stars < enemy_clan_stars:
                    status = "lose"
                else:
                    status = "draw"

                embed = discord.Embed(
                    title=f"War versus {enemy_clan_name} ended in **{status}**"
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
                                            or attack["defenderTag"]
                                            != atk["defenderTag"]
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

                guild = self.bot.get_guild(guild["guild_id"])
                channel = guild.get_channel(guild["coc_war_channel"])

                await channel.send(embed=embed)
