import discord
from discord import app_commands
from discord.ext import commands
from utils.config import set_news_channel

class ReconfigureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reconfigure", description="Update the news channel for FrostNews 24/7.")
    @app_commands.describe(channel="Select the new channel where news should be posted")
    async def reconfigure(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You must be an administrator to run this command.",
                ephemeral=True
            )
            return

        set_news_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"🔁 News channel updated to {channel.mention}.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ReconfigureCog(bot))
