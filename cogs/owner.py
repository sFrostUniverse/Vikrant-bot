import discord
from discord.ext import commands
from discord import app_commands

import os
from dotenv import load_dotenv

load_dotenv()
OWNER_ID = int(os.getenv("OWNER_ID"))


class Owner(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID
    
    @app_commands.command(name="say", description="Make Vikrant say a message (owner only)")
    @app_commands.check(is_owner)
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(message)

    @say.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.CheckFailure):
            await interaction.response.send_message("🚫 You’re not allowed to use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Owner(bot))



