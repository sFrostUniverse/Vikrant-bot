import discord
from discord.ext import commands
from discord import app_commands
import json

CONFIG_FILE = "data/config.json"

def get_complaint_channel_id(guild_id: int):
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id), {}).get("complaint_channel_id")
    except Exception:
        return None

class ComplaintModal(discord.ui.Modal, title="📢 Submit a Complaint"):
    complaint = discord.ui.TextInput(
        label="Describe your complaint",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        channel_id = get_complaint_channel_id(guild_id)
        channel = interaction.client.get_channel(channel_id) if channel_id else None

        if channel:
            embed = discord.Embed(
                title="📨 New Anonymous Complaint",
                description=self.complaint.value,
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Submitted anonymously by {interaction.user.display_name}")
            await channel.send(embed=embed)
            await interaction.response.send_message(
                "✅ Your complaint has been submitted anonymously.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Complaint channel not configured. Please contact an admin.",
                ephemeral=True
            )

class Complaints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="complain", description="Submit an anonymous complaint")
    async def complain(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ComplaintModal())

async def setup(bot):
    await bot.add_cog(Complaints(bot))
