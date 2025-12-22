import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime

class AntiNuke(Cog):
    """Basic anti-nuke protection (channel deletion)"""

    def __init__(self, bot):
        self.bot = bot
        self.action_log = {}  # guild_id -> user_id -> [timestamps]

    # ─────────────────────────────
    # INTERNAL UTILS
    # ─────────────────────────────
    def log_action(self, guild_id: int, user_id: int):
        now = datetime.datetime.utcnow()
        self.action_log.setdefault(guild_id, {})
        self.action_log[guild_id].setdefault(user_id, [])
        self.action_log[guild_id][user_id].append(now)

        # cleanup old entries (>30s)
        self.action_log[guild_id][user_id] = [
            t for t in self.action_log[guild_id][user_id]
            if (now - t).total_seconds() < 30
        ]

    def is_spam(self, guild_id: int, user_id: int, limit=3, seconds=10):
        actions = self.action_log.get(guild_id, {}).get(user_id, [])
        now = datetime.datetime.utcnow()
        recent = [a for a in actions if (now - a).total_seconds() < seconds]
        return len(recent) >= limit

    def is_protected(self, guild: discord.Guild, member: discord.Member):
        if member.id == guild.owner_id:
            return True
        if member.id == self.bot.user.id:
            return True
        return False

    # ─────────────────────────────
    # EVENT LISTENER
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel
