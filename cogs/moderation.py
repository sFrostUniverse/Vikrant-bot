import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await interaction.guild.ban(member, reason=reason)
            await interaction.response.send_message(
                f"✅ Banned {member.mention} for: **{reason}**", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to ban that member.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to ban member. Error: {e}", ephemeral=True
            )

    @app_commands.command(name="unban", description="Unban a user by their username#discriminator or user ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: Interaction, user: str):
        banned_users = await interaction.guild.bans()
        user_obj = None
        for ban_entry in banned_users:
            banned_user = ban_entry.user
            if str(banned_user.id) == user or f"{banned_user.name}#{banned_user.discriminator}" == user:
                user_obj = banned_user
                break

        if user_obj is None:
            await interaction.response.send_message("❌ User not found in the ban list.", ephemeral=True)
            return

        await interaction.guild.unban(user_obj)
        await interaction.response.send_message(f"✅ Unbanned {user_obj.name}#{user_obj.discriminator}", ephemeral=True)

    @ban.error
    async def ban_error(self, interaction: Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "🚫 You don't have permission to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ An unexpected error occurred: {error}", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
