import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
import os

CONFIG_FILE = "data/config.json"
os.makedirs("data", exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


class AntiNuke(commands.Cog):
    """Vikrant Anti-Nuke: Channel deletion protection"""

    def __init__(self, bot):
        self.bot = bot
        self.action_log = {}  # guild_id -> user_id -> [timestamps]

    # ─────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────
    def log_action(self, guild_id: int, user_id: int):
        now = datetime.now(timezone.utc)
        self.action_log.setdefault(guild_id, {})
        self.action_log[guild_id].setdefault(user_id, [])
        self.action_log[guild_id][user_id].append(now)

        # cleanup >30s
        self.action_log[guild_id][user_id] = [
            t for t in self.action_log[guild_id][user_id]
            if (now - t).total_seconds() < 30
        ]

    def is_spam(self, guild_id: int, user_id: int, limit=3, seconds=10):
        now = datetime.now(timezone.utc)
        actions = self.action_log.get(guild_id, {}).get(user_id, [])
        recent = [a for a in actions if (now - a).total_seconds() < seconds]
        return len(recent) >= limit

    def is_protected(self, guild: discord.Guild, user_id: int):
        cfg = load_config().get(str(guild.id), {})
        trusted = cfg.get("trusted_admins", [])

        return (
            user_id == guild.owner_id
            or user_id == self.bot.user.id
            or user_id in trusted
        )

    # ─────────────────────────────
    # EVENT LISTENER
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        actor = None

        # audit log lookup
        async for entry in guild.audit_logs(
            action=discord.AuditLogAction.channel_delete,
            limit=5
        ):
            if entry.target.id == channel.id:
                delta = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if delta <= 5:
                    actor = entry.user
                break

        if not actor:
            return  # cannot safely attribute

        if self.is_protected(guild, actor.id):
            return  # trusted / owner / bot

        # record action
        self.log_action(guild.id, actor.id)

        # anti-nuke threshold
        if self.is_spam(guild.id, actor.id):
            try:
                await guild.ban(
                    actor,
                    reason="Vikrant Anti-Nuke: Mass channel deletion"
                )
            except discord.Forbidden:
                pass
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
