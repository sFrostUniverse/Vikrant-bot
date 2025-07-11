import discord
from discord.ext import commands
from discord import app_commands
import json

CONFIG_FILE = "data/config.json"

def get_trusted_admins(guild_id: int):
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id), {}).get("trusted_admins", [])
    except Exception:
        return []

class Admins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="trusted_admins", description="Show the list of trusted admins for this server")
    async def trusted_admins(self, interaction: discord.Interaction):
        guild = interaction.guild
        trusted_ids = get_trusted_admins(guild.id)

        if not trusted_ids:
            await interaction.response.send_message(
                "⚠️ No trusted admins configured for this server.",
                ephemeral=True
            )
            return

        mentions = []
        for admin_id in trusted_ids:
            member = guild.get_member(admin_id)
            mentions.append(member.mention if member else f"`{admin_id}`")

        embed = discord.Embed(
            title="🛡 Trusted Admins",
            description="\n".join(mentions),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Managed by Vikrant Security Bot")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admins(bot))
