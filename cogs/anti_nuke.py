import discord
from discord.ext import commands
from discord.ext.commands import Cog
import asyncio
import datetime

class AntiNuke(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_log = {}  

    def log_action(self, guild_id, user_id):
        now = datetime.datetime.utcnow()
        if guild_id not in self.action_log:
            self.action_log[guild_id] = {}
        if user_id not in self.action_log[guild_id]:
            self.action_log[guild_id][user_id] = []
        self.action_log[guild_id][user_id].append(now)

    def check_spam(self, guild_id, user_id, limit=3, seconds=10):
        if guild_id in self.action_log and user_id in self.action_log[guild_id]:
            actions = self.action_log[guild_id][user_id]
            now = datetime.datetime.utcnow()
            recent = [a for a in actions if (now - a).total_seconds() < seconds]
            return len(recent) >= limit
        return False

@commands.Cog.listener()
async def on_guild_channel_delete(self, channel):
    guild = channel.guild
    entry = None
    async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        entry = log
        break

    if entry:
        user = entry.user
        self.log_action(guild.id, user.id)

        if self.check_spam(guild.id, user.id):
            try:
                await guild.ban(user, reason="Anti-Nuke: Mass channel deletion detected.")
                await guild.owner.send(f"⚠️ {user} was banned for nuking channels in `{guild.name}`.")
            except Exception as e:
                print(f"Failed to ban: {e}")


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
