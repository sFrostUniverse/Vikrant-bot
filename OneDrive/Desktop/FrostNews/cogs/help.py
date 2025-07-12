import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows all commands and usage for FrostNews 24/7")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📰 FrostNews 24/7 — Help Menu",
            description="Stay updated with breaking Indian news from multiple sources.\n\nHere are the available commands:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="/setup",
            value="Configure which channel receives auto-news updates. (Admin only)",
            inline=False
        )

        embed.add_field(
            name="/reconfigure",
            value="Update the news channel if needed. (Admin only)",
            inline=False
        )

        embed.add_field(
            name="/news",
            value="Fetch the latest top Indian news manually from Indian Express and NDTV.",
            inline=False
        )

        embed.add_field(
            name="/help",
            value="Display this help message.",
            inline=False
        )

        embed.set_footer(text="FrostNews 24/7 • Built by Sehaj and Chloe")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
