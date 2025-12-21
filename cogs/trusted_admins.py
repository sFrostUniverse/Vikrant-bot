import discord
from discord.ext import commands
from discord import app_commands

from utils.config import (
    load_config,
    save_config,
    get_guild_config,
    is_setup_owner_or_server_owner
)

class Admins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 📋 LIST TRUSTED ADMINS
    @app_commands.command(
        name="trusted_admins",
        description="Show the list of trusted admins for this server"
    )
    async def trusted_admins(self, interaction: discord.Interaction):
        guild_data = get_guild_config(interaction.guild.id)

        if not guild_data or not guild_data.get("trusted_admins"):
            await interaction.response.send_message(
                "⚠️ No trusted admins configured for this server.",
                ephemeral=True
            )
            return

        mentions = []
        for admin_id in guild_data["trusted_admins"]:
            member = interaction.guild.get_member(admin_id)
            mentions.append(member.mention if member else f"`{admin_id}`")

        embed = discord.Embed(
            title="🛡 Trusted Admins",
            description="\n".join(mentions),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Managed by Vikrant Security Bot")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ➕ ADD TRUSTED ADMIN
    @app_commands.command(
        name="add_trusted_admin",
        description="Add a trusted admin (setup owner only)"
    )
    @app_commands.check(is_setup_owner_or_server_owner)
    async def add_trusted_admin(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        data = load_config()
        guild_id = str(interaction.guild.id)
        guild_data = data.get(guild_id)

        if not member.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ User must have Administrator permission.",
                ephemeral=True
            )
            return

        if member.id in guild_data["trusted_admins"]:
            await interaction.response.send_message(
                "⚠️ User is already a trusted admin.",
                ephemeral=True
            )
            return

        guild_data["trusted_admins"].append(member.id)
        save_config(data)

        await interaction.response.send_message(
            f"✅ {member.mention} added as trusted admin.",
            ephemeral=True
        )

    # ➖ REMOVE TRUSTED ADMIN
    @app_commands.command(
        name="remove_trusted_admin",
        description="Remove a trusted admin (setup owner only)"
    )
    @app_commands.check(is_setup_owner_or_server_owner)
    async def remove_trusted_admin(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        data = load_config()
        guild_id = str(interaction.guild.id)
        guild_data = data.get(guild_id)

        if member.id not in guild_data["trusted_admins"]:
            await interaction.response.send_message(
                "❌ User is not a trusted admin.",
                ephemeral=True
            )
            return

        if member.id == guild_data["setup_owner_id"]:
            await interaction.response.send_message(
                "🚫 Cannot remove the setup owner.",
                ephemeral=True
            )
            return

        guild_data["trusted_admins"].remove(member.id)
        save_config(data)

        await interaction.response.send_message(
            f"🗑️ {member.mention} removed from trusted admins.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Admins(bot))
