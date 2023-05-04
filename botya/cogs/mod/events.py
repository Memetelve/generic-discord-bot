import time
import discord
import traceback

from discord.ext import commands

from botya.cache import _cache
from botya.core.utils.embed import Embed
from botya.core.db.db import Database


class ModEvents(commands.Cog):
    @commands.Cog.listener()
    async def on_member_join(self, member):
        timezone = await Database.get_timezone(member.guild.id)
        try:
            channel_id, active = await Database.get_log_settings(
                member.guild.id, "member_joined"
            )

            channel = member.guild.get_channel(channel_id)

            if channel and active:
                age = int(round(time.mktime(member.created_at.timetuple()), 0))
                embed = Embed(
                    title="",
                    color=0x215520,
                    description=f"{member.mention} joined the server!\nAccount created: <t:{age}> - <t:{age}:R>",
                    footer=[f"User ID: {member.id}", ""],
                    timestamp=True,
                    timezone=timezone,
                )
                await channel.send(embed=embed)
        except Exception:
            pass

        try:
            autoroles = await Database.get_autoroles(member.guild.id)

            roles = [member.guild.get_role(role) for role in autoroles]
            await member.add_roles(*roles)
        except Exception:
            pass

        if member.bot:
            return

        inviter, code = await self.tracker.fetch_inviter(member)

        try:
            msg, channel_id, active = await Database.get_welcome_message(
                member.guild.id
            )

            channel = member.guild.get_channel(channel_id)
            if channel and active:
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

                msg = msg.replace("[user]", member.mention)
                msg = msg.replace("[userName]", member.name)
                msg = msg.replace("[memberCount]", str(len(member.guild.members)))
                msg = msg.replace("[server]", member.guild.name)
                msg = msg.replace("[nl]", "\n")
                msg = msg.replace("[inviter]", inviter.mention)
                msg = msg.replace("[inviterName]", inviter.name)
                msg = msg.replace("[inviteCount]", str(real))

                await channel.send(msg)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id, active = await Database.get_log_settings(
            member.guild.id, "member_left"
        )
        timezone = await Database.get_timezone(member.guild.id)

        channel = member.guild.get_channel(channel_id)

        if channel and active:
            age = int(round(time.mktime(member.joined_at.timetuple()), 0))
            embed = Embed(
                title="",
                color=0x943A3B,
                description=f"{member.mention} left the server!\nJoined: <t:{age}> - <t:{age}:R>",
                footer=[f"User ID: {member.id}", ""],
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel_id, active = await Database.get_log_settings(guild.id, "member_banned")
        timezone = await Database.get_timezone(guild.id)

        channel = guild.get_channel(channel_id)

        if not channel or not active:
            return
        try:
            entries = [
                entry
                async for entry in guild.audit_logs(
                    limit=20, action=discord.AuditLogAction.ban
                )
            ]
            for ent in entries:
                if ent.target == user:
                    entry = ent
                    break

            embed = Embed(
                title="Member banned",
                color=0x000000,
                description=f"`User:` {user.name}#{user.discriminator}(`{user.id}`)\n`Admin:` {entry.user.name}{entry.user.discriminator}\n`Reason:` {entry.reason}",
                timestamp=True,
                timezone=timezone,
            )
        except Exception:
            traceback.print_exc()
            embed = Embed(
                title="",
                color=0x000000,
                description=f"{user.mention} has been banned from the server the server!\n",
                footer=[f"User ID: {user.id}", ""],
                timestamp=True,
                timezone=timezone,
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel_id, active = await Database.get_log_settings(
            guild.id, "member_unbanned"
        )
        timezone = await Database.get_timezone(guild.id)

        channel = guild.get_channel(channel_id)

        if channel and active:
            embed = Embed(
                title="",
                color=0xFFFFFF,
                description=f"{user.mention} has been unbanned from the server the server!\n",
                footer=[f"User ID: {user.id}", ""],
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        timezone = await Database.get_timezone(before.guild.id)

        if before.nick != after.nick:
            channel_id, active = await Database.get_log_settings(
                before.guild.id, "member_nickname_changed"
            )

            channel = before.guild.get_channel(channel_id)

            if not before.nick:
                before.nick = before.name

            if not after.nick:
                after.nick = before.name

            if channel and active:
                embed = Embed(
                    title="",
                    color=0x81C3C4,
                    description=f"{before.mention} has changed nickname from `{before.nick}` to `{after.nick}`",
                    footer=[f"User ID: {before.id}", ""],
                    timestamp=True,
                    timezone=timezone,
                )
                await channel.send(embed=embed)

        if before.roles != after.roles:
            if len(before.roles) < len(after.roles):
                channel_id, active = await Database.get_log_settings(
                    before.guild.id, "member_received_role"
                )

                channel = before.guild.get_channel(channel_id)

                if channel and active:
                    roles = list(set(after.roles) - set(before.roles))

                    role_str = "".join(f"{role.mention}, " for role in roles)

                    embed = Embed(
                        title="",
                        color=0x276B05,
                        description=f"{before.mention} has received role(s) {role_str}",
                        footer=[f"User ID: {before.id}", ""],
                        timestamp=True,
                        timezone=timezone,
                    )
                    await channel.send(embed=embed)

            elif len(before.roles) > len(after.roles):
                channel_id, active = await Database.get_log_settings(
                    before.guild.id, "member_lost_role"
                )

                channel = before.guild.get_channel(channel_id)

                if channel and active:
                    roles = list(set(before.roles) - set(after.roles))

                    role_str = "".join(f"{role.mention}, " for role in roles)

                    embed = Embed(
                        title="",
                        color=0x6B1805,
                        description=f"{before.mention} has lost role(s) {role_str}",
                        footer=[f"User ID: {before.id}", ""],
                        timestamp=True,
                        timezone=timezone,
                    )
                    await channel.send(embed=embed)

        if before.timed_out_until != after.timed_out_until:
            channel_id, active = await Database.get_log_settings(
                before.guild.id, "timeout_given_or_removed"
            )

            channel = before.guild.get_channel(channel_id)

            if channel and active:
                if after.timed_out_until:
                    age = int(round(time.mktime(after.timed_out_until.timetuple()), 0))

                    embed = Embed(
                        title="",
                        color=0x400000,
                        description=f"{before.mention} was timed out.\nEnd of this timeout <t:{age}> - <t:{age}:R>",
                        timestamp=True,
                        timezone=timezone,
                    )

                elif before.timed_out_until:
                    age = int(round(time.mktime(before.timed_out_until.timetuple()), 0))

                    embed = Embed(
                        title="",
                        color=0x000040,
                        description=f"Timeout of {before.mention} was removed by admin\n That timeout was supposed to end <t:{age}> - <t:{age}:R>",
                        timestamp=True,
                        timezone=timezone,
                    )

                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel_p):
        channel_id, active = await Database.get_log_settings(
            channel_p.guild.id, "channel_created"
        )
        timezone = await Database.get_timezone(channel_p.guild.id)

        channel = channel_p.guild.get_channel(channel_id)

        if channel and active:
            if channel_p.category:
                text = f"in category `{channel_p.category}`"
            else:
                text = "without a category"

            embed = Embed(
                title="",
                color=0x03FEFF,
                description=f"Channel {channel_p.mention} was created {text}",
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel_p):
        channel_id, active = await Database.get_log_settings(
            channel_p.guild.id, "channel_deleted"
        )
        timezone = await Database.get_timezone(channel_p.guild.id)

        channel = channel_p.guild.get_channel(channel_id)

        if channel and active:
            if channel_p.category:
                text = f"from category `{channel_p.category}`"
            else:
                text = "(had no category)"

            embed = Embed(
                title="",
                color=0x000747,
                description=f"Channel **{channel_p.name}** was deleted {text}",
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        channel_id, active = await Database.get_log_settings(
            role.guild.id, "role_created"
        )
        timezone = await Database.get_timezone(role.guild.id)

        channel = role.guild.get_channel(channel_id)

        if channel and active:
            embed = Embed(
                title="",
                color=0x03FEFF,
                description=f"Role {role.mention} was created",
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        channel_id, active = await Database.get_log_settings(
            role.guild.id, "role_deleted"
        )
        timezone = await Database.get_timezone(role.guild.id)

        channel = role.guild.get_channel(channel_id)

        if channel and active:
            embed = Embed(
                title="",
                color=0x000747,
                description=f"Role **{role.name}** was deleted",
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return

        channel_id, active = await Database.get_log_settings(
            message.guild.id, "message_deleted"
        )
        timezone = await Database.get_timezone(message.guild.id)

        channel = message.guild.get_channel(channel_id)

        if (
            channel
            and active
            and (len(message.content) > 0 or _cache.get(message.id, None))
        ):
            image_url = _cache.get(message.id, None)
            if image_url:
                image_url = image_url[0]

            embed = Embed(
                title="",
                color=0x010101,
                description=f"message by {message.author.mention} was deleted in channel {message.channel.mention}",
                fields=[["Message content", message.content]],
                timestamp=True,
                timezone=timezone,
                image=image_url,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # check if guild
        if not getattr(before, "guild", None):
            return

        channel_id, active = await Database.get_log_settings(
            before.guild.id, "message_edited"
        )
        timezone = await Database.get_timezone(before.guild.id)

        channel = before.guild.get_channel(channel_id)

        if channel and active and before.content != after.content:
            embed = Embed(
                title="",
                color=0x010101,
                description=f"message by {before.author.mention} was edited in channel {before.channel.mention}",
                fields=[
                    ["Message before", before.content],
                    ["Message after", after.content],
                ],
                timestamp=True,
                timezone=timezone,
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        timezone = await Database.get_timezone(member.guild.id)

        if before.channel is None and after.channel is not None:
            channel_id, active = await Database.get_log_settings(
                member.guild.id, "member_joined_voice_channel"
            )

            channel = member.guild.get_channel(channel_id)

            if channel and active:
                # create embed with info that member joined voice channel
                embed = Embed(
                    title="",
                    description=f"{member.mention} has joined *{after.channel.name}*",
                    color=0xBEBEBE,
                    timestamp=True,
                    timezone=timezone,
                )
                await channel.send(embed=embed)

        elif before.channel is not None and after.channel is None:
            channel_id, active = await Database.get_log_settings(
                member.guild.id, "member_left_voice_channel"
            )

            channel = member.guild.get_channel(channel_id)

            if channel and active:
                # crete embed with info that member left voice channel
                embed = Embed(
                    title="",
                    description=f"{member.mention} has left *{before.channel.name}*",
                    color=0x000,
                    timestamp=True,
                    timezone=timezone,
                )
                await channel.send(embed=embed)

        elif before.channel is not None and before.channel != after.channel:
            channel_id, active = await Database.get_log_settings(
                member.guild.id, "member_switched_voice_channel"
            )

            channel = member.guild.get_channel(channel_id)

            if channel and active:
                # create embed with info that member changed voice channel
                embed = Embed(
                    title="",
                    description=f"{member.mention} has changed voice channel from *{before.channel.name}* to *{after.channel.name}*",
                    color=0x736F6C,
                    timestamp=True,
                    timezone=timezone,
                )

                await channel.send(embed=embed)
