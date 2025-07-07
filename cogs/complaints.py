import discord
from discord.ext import commands
from discord import app_commands

COMPLAINT_CHANNEL_ID = 1390696570680377457

class ComplaintModal(discord.ui.Modal, title="📢 Submit a Complaint"):
    complaint = discord.ui.TextInput(
        label="Describe your complaint",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.client.get_channel(COMPLAINT_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="📨 New Anonymous Complaint",
                description=self.complaint.value,
                color=discord.Color.orange()
            )
            embed.set_footer(text="Submitted anonymously")
            await channel.send(embed=embed)
            await interaction.response.send_message(
                "✅ Your complaint has been submitted anonymously.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Could not send the complaint. Please try again later.",
                ephemeral=True
            )

class Complaints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ❌ Do NOT manually add self.bot.tree.add_command(...) here

    @app_commands.command(name="complain", description="Submit an anonymous complaint")
    async def complain(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ComplaintModal())

async def setup(bot):
    await bot.add_cog(Complaints(bot))
