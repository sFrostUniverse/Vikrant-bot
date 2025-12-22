import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone

CONFIG_FILE = "data/config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


class AuditWatcher(commands.Cog):
    """Dyno-style security audit watcher (no punish, alerts only)"""

    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────
    # UTIL
    # ─────────────────────────────
    async def log_action(self, guild: discord.Guild, message: str):
        config = load_config().get(str(guild.id), {})
        channel_id = config.get("admin_channel_id")

        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="🚨 Security Alert",
            description=message,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Vikrant Security")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    def is_trusted(self, guild: discord.Guild, user: discord.User):
        config = load_config().get(str(guild.id), {})
        trusted = config.get("trusted_admins", [])

        if user.id == guild.owner_id:
            return True
        if user.id == self.bot.user.id:
            return True

        return user.id in trusted

    async def recent_entry(self, guild, action):
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                # must be very recent
                delta = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if delta <= 5:
                    return entry
        except discord.Forbidden:
            return None
        return None

    # ─────────────────────────────
    # EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild

        entry = await self.recent_entry(
            guild,
            discord.AuditLogAction.channel_delete
        )
        if not entry or self.is_trusted(guild, entry.user):
            return

        await self.log_action(
            guild,
            f"🟥 **{entry.user}** deleted channel **#{channel.name}**"
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild

        entry = await self.recent_entry(
            guild,
            discord.AuditLogAction.role_delete
        )
        if not entry or self.is_trusted(guild, entry.user):
            return

        await self.log_action(
            guild,
            f"🟥 **{entry.user}** deleted role **{role.name}**"
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        entry = await self.recent_entry(
            guild,
            discord.AuditLogAction.ban
        )
        if not entry or self.is_trusted(guild, entry.user):
            return

        await self.log_action(
            guild,
            f"🚫 **{entry.user}** banned **{user}**"
        )


async def setup(bot):
    await bot.add_cog(AuditWatcher(bot))
