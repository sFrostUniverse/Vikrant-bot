import discord
from discord import app_commands
from discord.ext import commands
from utils.config import set_news_channel, get_news_channel

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure FrostNews 24/7 for your server.")
    @app_commands.describe(channel="Select the channel where news should be posted")
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You must be an administrator to run this command.",
                ephemeral=True
            )
            return

        current = get_news_channel(interaction.guild_id)
        if current:
            await interaction.response.send_message(
                "⚠️ This server is already configured. Use `/reconfigure` to update the channel.",
                ephemeral=True
            )
            return

        set_news_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"✅ FrostNews will now post updates in {channel.mention}.",
            ephemeral=True
        )
        print(f"[Setup] FrostNews configured for {interaction.guild.name} ({interaction.guild_id})")

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
