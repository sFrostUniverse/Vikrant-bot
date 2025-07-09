import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta

CONFIG_FILE = "data/config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

class AuditWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    async def log_action(self, guild: discord.Guild, message: str):
        config = self.config.get(str(guild.id), {})
        admin_channel_id = config.get("admin_channel_id")
        if not admin_channel_id:
            return

        channel = guild.get_channel(admin_channel_id)
        if channel:
            embed = discord.Embed(
                title="🚨 Security Alert",
                description=message,
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if (datetime.utcnow() - entry.created_at).seconds > 5:
                return
            if str(entry.user.id) in self.config.get(str(guild.id), {}).get("trusted_admins", []):
                return

            await self.log_action(guild, f"🔴 **{entry.user}** deleted channel **#{channel.name}**")
            # Later: punish logic

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if (datetime.utcnow() - entry.created_at).seconds > 5:
                return
            if str(entry.user.id) in self.config.get(str(guild.id), {}).get("trusted_admins", []):
                return

            await self.log_action(guild, f"🟥 **{entry.user}** deleted role **{role.name}**")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if (datetime.utcnow() - entry.created_at).seconds > 5:
                return
            if str(entry.user.id) in self.config.get(str(guild.id), {}).get("trusted_admins", []):
                return

            await self.log_action(guild, f"🚫 **{entry.user}** banned **{user}**")

async def setup(bot):
    await bot.add_cog(AuditWatcher(bot))
