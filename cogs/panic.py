import discord
from discord.ext import commands
from discord import app_commands, Interaction
import json, os

CONFIG_FILE = "data/config.json"
BACKUP_FILE = "data/permissions_backup.json"

def get_admin_channel_id(guild_id: int):
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    return data.get(str(guild_id), {}).get("admin_log_channel")

def save_backup(guild_id, roles_backup):
    if not os.path.exists("data"):
        os.makedirs("data")
    try:
        with open(BACKUP_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[str(guild_id)] = roles_backup
    with open(BACKUP_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_backup(guild_id):
    if not os.path.exists(BACKUP_FILE):
        return {}
    with open(BACKUP_FILE, "r") as f:
        data = json.load(f)
    return data.get(str(guild_id), {})

class Panic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.locked_channels = {}

    @app_commands.command(name="panic", description="🚨 Emergency lockdown – locks all channels & disables risky perms.")
    @app_commands.checks.has_permissions(administrator=True)
    async def panic(self, interaction: Interaction):
        guild = interaction.guild
        admin_channel_id = get_admin_channel_id(guild.id)
        locked_channels = []
        roles_backup = {}

        for channel in guild.channels:
            overwrite = channel.overwrites_for(guild.default_role)
            if isinstance(channel, discord.TextChannel):
                overwrite.send_messages = False
            elif isinstance(channel, discord.VoiceChannel):
                overwrite.connect = False
            try:
                await channel.set_permissions(guild.default_role, overwrite=overwrite)
                locked_channels.append(channel.id)
            except Exception as e:
                print(f"Failed to lock {channel.name}: {e}")

        self.locked_channels[guild.id] = locked_channels

        dangerous_perms = [
            "manage_channels", "ban_members", "kick_members", "administrator",
            "manage_roles", "manage_guild", "manage_webhooks", "mention_everyone"
        ]

        for role in guild.roles:
            if role.is_default() or role.managed:
                continue
            perms = role.permissions
            original = perms.value
            changed = False
            for perm in dangerous_perms:
                if getattr(perms, perm):
                    setattr(perms, perm, False)
                    changed = True
            if changed:
                try:
                    await role.edit(permissions=perms)
                    roles_backup[str(role.id)] = original
                except Exception as e:
                    print(f"Failed to edit role {role.name}: {e}")

        save_backup(guild.id, roles_backup)

        if admin_channel_id:
            admin_channel = guild.get_channel(admin_channel_id)
            if admin_channel:
                embed = discord.Embed(
                    title="🚨 Panic Mode Activated!",
                    description=f"{interaction.user.mention} has initiated a full emergency lockdown.",
                    color=discord.Color.red()
                )
                embed.add_field(name="🔒 Channels Locked", value=f"{len(locked_channels)}", inline=True)
                embed.add_field(name="⚠️ Roles Restricted", value=f"{len(roles_backup)}", inline=True)
                embed.set_footer(text="Vikrant • Emergency Response")
                await admin_channel.send(embed=embed)

        await interaction.response.send_message(
            "🚨 Panic mode activated. All channels locked and dangerous permissions revoked.",
            ephemeral=True
        )

    @app_commands.command(name="unpanic", description="🔓 Revert panic mode – unlocks all channels & restores roles.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unpanic(self, interaction: Interaction):
        guild = interaction.guild
        admin_channel_id = get_admin_channel_id(guild.id)
        restored_roles = 0
        unlocked_channels = 0

        channel_ids = self.locked_channels.get(guild.id, [])
        for channel in guild.channels:
            if channel.id in channel_ids:
                try:
                    overwrite = channel.overwrites_for(guild.default_role)
                    if isinstance(channel, discord.TextChannel):
                        overwrite.send_messages = None
                    elif isinstance(channel, discord.VoiceChannel):
                        overwrite.connect = None
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    unlocked_channels += 1
                except:
                    continue

        backup = load_backup(guild.id)
        for role_id, perm_value in backup.items():
            role = guild.get_role(int(role_id))
            if role:
                try:
                    perms = discord.Permissions(perm_value)
                    await role.edit(permissions=perms)
                    restored_roles += 1
                except:
                    continue

        if admin_channel_id:
            admin_channel = guild.get_channel(admin_channel_id)
            if admin_channel:
                embed = discord.Embed(
                    title="🔓 Panic Mode Deactivated",
                    description=f"{interaction.user.mention} has restored normal server operation.",
                    color=discord.Color.green()
                )
                embed.add_field(name="✅ Channels Unlocked", value=str(unlocked_channels), inline=True)
                embed.add_field(name="🔁 Roles Restored", value=str(restored_roles), inline=True)
                embed.set_footer(text="Vikrant • Emergency Recovery")
                await admin_channel.send(embed=embed)

        await interaction.response.send_message("🔓 Panic mode reverted. Server restored.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Panic(bot))
