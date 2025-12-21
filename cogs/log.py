import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime, timezone

# ─────────────────────────────
# PATHS
# ─────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE_DIR, "data", "logging.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)

# ─────────────────────────────
# COLORS (Vikrant Compact)
# ─────────────────────────────
NAVY = discord.Color.from_rgb(0, 31, 63)
GREY = discord.Color.from_rgb(108, 122, 137)
OK   = discord.Color.from_rgb(46, 204, 113)
WARN = discord.Color.from_rgb(255, 153, 51)
ALRT = discord.Color.from_rgb(192, 57, 43)

def utc_now():
    return datetime.now(timezone.utc)


class Logs(commands.Cog):
    """Vikrant Persistent Logging System"""

    def __init__(self, bot):
        self.bot = bot
        self.inv_cache = {}
        self._db_init()
        self.bot.loop.create_task(self._load_invites())

    # ─────────────────────────────
    # DATABASE
    # ─────────────────────────────
    def db(self):
        return sqlite3.connect(DB)

    def _db_init(self):
        con = self.db()
        cur = con.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            guild_id INTEGER,
            code TEXT,
            inviter_id INTEGER,
            uses INTEGER,
            PRIMARY KEY(guild_id, code)
        )""")

        con.commit()
        con.close()

    def set_log(self, gid, cid):
        con = self.db()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO logs VALUES (?,?)", (gid, cid))
        con.commit()
        con.close()

    def get_log(self, gid):
        con = self.db()
        cur = con.cursor()
        cur.execute("SELECT channel_id FROM logs WHERE guild_id=?", (gid,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else None

    def save_inv(self, gid, code, inviter, uses):
        con = self.db()
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO invites VALUES (?,?,?,?)",
            (gid, code, inviter, uses)
        )
        con.commit()
        con.close()

    # ─────────────────────────────
    # EMBED / SEND
    # ─────────────────────────────
    def embed(self, title, color, user=None):
        e = discord.Embed(
            title=f"Vikrant • {title}",
            color=color,
            timestamp=utc_now()
        )
        if user:
            e.set_author(name=user, icon_url=user.display_avatar.url)
        else:
            e.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
        e.set_footer(text="Vikrant Logs")
        return e

    async def send(self, guild, embed):
        cid = self.get_log(guild.id)
        if not cid:
            return
        ch = guild.get_channel(cid)
        if ch:
            try:
                await ch.send(embed=embed)
            except:
                pass

    # ─────────────────────────────
    # INVITE CACHE
    # ─────────────────────────────
    async def _load_invites(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds:
            try:
                invs = await g.invites()
            except:
                continue

            cache = {}
            for i in invs:
                inviter = i.inviter.id if i.inviter else None
                cache[i.code] = (i.uses, inviter)
                self.save_inv(g.id, i.code, inviter, i.uses)

            self.inv_cache[g.id] = cache

    # ─────────────────────────────
    # SLASH COMMANDS
    # ─────────────────────────────
from typing import Literal

@app_commands.command(name="logs", description="Configure Vikrant logs")
@app_commands.describe(
    action="What do you want to do?",
    channel="Log channel (required for set)"
)
async def logs(
    self,
    inter: discord.Interaction,
    action: Literal["set", "show", "disable"],
    channel: discord.TextChannel = None
):
    if action == "set":
        if not channel:
            return await inter.response.send_message(
                "❌ Please provide a channel.",
                ephemeral=True
            )
        self.set_log(inter.guild.id, channel.id)
        return await inter.response.send_message(
            f"✅ Logging enabled in {channel.mention}",
            ephemeral=True
        )

    if action == "show":
        cid = self.get_log(inter.guild.id)
        return await inter.response.send_message(
            f"📄 Log channel: <#{cid}>" if cid else "⚠️ No log channel set.",
            ephemeral=True
        )

    if action == "disable":
        self.set_log(inter.guild.id, None)
        return await inter.response.send_message(
            "🛑 Logging disabled.",
            ephemeral=True
        )


    # ─────────────────────────────
    # EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.guild or msg.author.bot:
            return

        e = self.embed("Message Deleted", ALRT, msg.author)
        e.add_field(name="User", value=msg.author.mention, inline=False)
        e.add_field(name="Channel", value=msg.channel.mention, inline=False)

        if msg.content:
            e.add_field(name="Content", value=msg.content[:300], inline=False)

        if msg.attachments:
            for a in msg.attachments:
                e.add_field(name="Attachment", value=a.url, inline=False)

        await self.send(msg.guild, e)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        e = self.embed("Message Edited", WARN, before.author)
        e.add_field(name="Channel", value=before.channel.mention, inline=False)
        e.add_field(name="Before", value=before.content[:300], inline=False)
        e.add_field(name="After", value=after.content[:300], inline=False)

        await self.send(before.guild, e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Nickname
        if before.nick != after.nick:
            actor = None
            async for entry in after.guild.audit_logs(
                action=discord.AuditLogAction.member_update,
                limit=5
            ):
                if entry.target.id == after.id:
                    actor = entry.user
                    break

            e = self.embed("Nickname Changed", WARN, after)
            e.add_field(name="User", value=after.mention, inline=False)
            e.add_field(name="Changed By", value=actor.mention if actor else "Unknown", inline=False)
            e.add_field(name="Before", value=before.nick or before.name, inline=True)
            e.add_field(name="After", value=after.nick or after.name, inline=True)
            await self.send(after.guild, e)

        # Roles
        if before.roles != after.roles:
            added = set(after.roles) - set(before.roles)
            removed = set(before.roles) - set(after.roles)

            actor = None
            async for entry in after.guild.audit_logs(
                action=discord.AuditLogAction.member_role_update,
                limit=5
            ):
                if entry.target.id == after.id:
                    actor = entry.user
                    break

            e = self.embed("Roles Updated", WARN, after)
            e.add_field(name="User", value=after.mention, inline=False)
            e.add_field(name="Changed By", value=actor.mention if actor else "Unknown", inline=False)

            if added:
                e.add_field(name="Added", value=", ".join(r.name for r in added), inline=False)
            if removed:
                e.add_field(name="Removed", value=", ".join(r.name for r in removed), inline=False)

            await self.send(after.guild, e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, m, b, a):
        if b.channel == a.channel:
            return

        actor = None
        async for entry in m.guild.audit_logs(
            action=discord.AuditLogAction.member_move,
            limit=5
        ):
            if entry.target.id == m.id:
                actor = entry.user
                break

        if b.channel and a.channel:
            e = self.embed("Voice Move", NAVY, m)
            e.add_field(name="User", value=m.mention, inline=False)
            e.add_field(name="Moved By", value=actor.mention if actor else "Self", inline=False)
            e.add_field(name="From", value=b.channel.name, inline=True)
            e.add_field(name="To", value=a.channel.name, inline=True)
            await self.send(m.guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
