import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone

CONFIG_FILE = "data/config.json"


# ─────────────────────────────
# CONFIG
# ─────────────────────────────
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_log_channel(guild: discord.Guild):
    cfg = load_config().get(str(guild.id))
    if not cfg:
        return None
    return guild.get_channel(cfg.get("log_channel_id"))


# ─────────────────────────────
# LOGS COG
# ─────────────────────────────
class Logs(commands.Cog):
    """Dyno-style logging (full voice + moderation parity)"""

    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}
        bot.loop.create_task(self.cache_invites())

    # ─────────────────────────────
    # UTIL
    # ─────────────────────────────
    async def send_log(self, guild, embed):
        channel = get_log_channel(guild)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    def base(self, title, color, user=None, big_avatar=False):
        e = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        e.set_footer(text="Vikrant Logs")

        if user:
            e.set_author(
                name=str(user),
                icon_url=user.display_avatar.url
            )
            if big_avatar:
                e.set_thumbnail(url=user.display_avatar.url)

        return e

    async def recent_audit(self, guild, action, target_id=None):
        if not guild.me.guild_permissions.view_audit_log:
            return None

        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                delta = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if delta <= 5:
                    if target_id is None or entry.target.id == target_id:
                        return entry
        except:
            pass
        return None

    # ─────────────────────────────
    # INVITES
    # ─────────────────────────────
    async def cache_invites(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds:
            try:
                self.invite_cache[g.id] = await g.invites()
            except:
                self.invite_cache[g.id] = []

    # ─────────────────────────────
    # MEMBER JOIN / LEAVE
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        inviter = None
        code = None

        try:
            new_invites = await guild.invites()
        except:
            new_invites = []

        old_invites = self.invite_cache.get(guild.id, [])

        for old in old_invites:
            for new in new_invites:
                if old.code == new.code and new.uses > old.uses:
                    inviter = new.inviter
                    code = f"{new.code} ({old.uses} → {new.uses})"
                    break

        self.invite_cache[guild.id] = new_invites

        created = member.created_at
        age_days = (datetime.now(timezone.utc) - created).days

        e = self.base("Member Joined", discord.Color.green(), member, big_avatar=True)
        e.add_field(name="User", value=member.mention, inline=False)
        e.add_field(name="Account Age", value=f"{age_days} days", inline=False)

        if inviter:
            e.add_field(name="Invited By", value=inviter.mention, inline=False)
            e.add_field(name="Code", value=code, inline=False)
        else:
            e.add_field(name="Invite", value="Unknown / Vanity / Offline", inline=False)

        await self.send_log(guild, e)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        e = self.base("Member Left", discord.Color.orange(), member, big_avatar=True)
        e.add_field(name="User", value=member.mention, inline=False)
        await self.send_log(member.guild, e)

    # ─────────────────────────────
    # MESSAGE LOGS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.guild or msg.author.bot:
            return

        e = self.base("Message Deleted", discord.Color.red(), msg.author)
        e.add_field(name="Channel", value=msg.channel.mention, inline=False)

        if msg.content:
            e.add_field(name="Content", value=msg.content[:500], inline=False)

        for a in msg.attachments:
            e.add_field(name="Attachment", value=a.url, inline=False)

        await self.send_log(msg.guild, e)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        e = self.base("Message Edited", discord.Color.orange(), before.author)
        e.add_field(name="Channel", value=before.channel.mention, inline=False)
        e.add_field(name="Before", value=before.content[:300], inline=False)
        e.add_field(name="After", value=after.content[:300], inline=False)

        await self.send_log(before.guild, e)

    # ─────────────────────────────
    # VOICE EVENTS (FULL)
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # ignore no-op
        if before.channel == after.channel:
            return

        guild = member.guild
        actor = None

        # check audit logs ONLY for moves
        async for entry in guild.audit_logs(
            action=discord.AuditLogAction.member_move,
            limit=5
        ):
            # must match target
            if entry.target.id != member.id:
                continue

            # must be recent (≤5 seconds)
            delta = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
            if delta > 5:
                continue

            # actor can be same as member (mod moved themselves)
            actor = entry.user
            break

        # build embed
        e = self.base(
            "Voice Channel Moved",
            discord.Color.blurple(),
            member
        )

        e.add_field(
            name="User",
            value=member.mention,
            inline=False
        )

        e.add_field(
            name="From",
            value=before.channel.name if before.channel else "None",
            inline=True
        )
        e.add_field(
            name="To",
            value=after.channel.name if after.channel else "None",
            inline=True
        )

        # 🔥 ONLY add this field if a moderator actually moved someone
        if actor:
            e.add_field(
                name="Moved By",
                value=actor.mention,
                inline=False
            )

        await self.send(guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
