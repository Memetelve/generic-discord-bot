import discord
from discord import app_commands

class emojiTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str):
        pass
