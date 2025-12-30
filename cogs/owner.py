import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()
OWNER_ID = int(os.getenv("OWNER_ID"))


# ─────────────────────────────
# PERMISSION CHECK (STANDALONE)
# ─────────────────────────────
def can_say(interaction: discord.Interaction) -> bool:
    # Global bot owner (you)
    if interaction.user.id == OWNER_ID:
        return True

    # Must be inside a guild
    if not interaction.guild:
        return False

    # Server owner
    if interaction.user.id == interaction.guild.owner_id:
        return True

    # Server admin
    return interaction.user.guild_permissions.administrator


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────
    # COMMAND
    # ─────────────────────────────
    @app_commands.command(
        name="say",
        description="Make Vikrant say a message (Admins only)"
    )
    @app_commands.check(can_say)
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(message)

    # ─────────────────────────────
    # ERROR HANDLER
    # ─────────────────────────────
    @say.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(
                    "🚫 You must be a **server admin** to use this command.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "🚫 You must be a **server admin** to use this command.",
                    ephemeral=True
                )


async def setup(bot):
    await bot.add_cog(Owner(bot))
