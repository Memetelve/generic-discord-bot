import time
import discord
import traceback
import json

from discord.ext import commands

from botya.core.utils.embed import Embed
from botya.core.db.db import Database


class AdminEvents(commands.Cog):
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            if member.bot:
                return

            inviter, code = await self.tracker.fetch_inviter(member)
            if inviter is None or code is None:
                return

            await Database.add_invite(member.guild.id, member.id, inviter.id, code)
        except Exception:
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await Database.make_invite_leave(member.guild.id, member.id)
