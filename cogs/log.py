import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime, timezone

# ─────────────────────────────
# RENDER PERSISTENT PATH
# ─────────────────────────────
DATA_DIR = "/data"
DB = os.path.join(DATA_DIR, "logging.db")
os.makedirs(DATA_DIR, exist_ok=True)

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
            PRIMARY KEY (guild_id, code)
        )""")

        con.commit()
        con.close()

    def set_log(self, gid, cid):
        con = self.db()
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO logs VALUES (?,?)",
            (gid, cid)
        )
        con.commit()
        con.close()

    def get_log(self, gid):
        con = self.db()
        cur = con.cursor()
        cur.execute(
            "SELECT channel_id FROM logs WHERE guild_id=?",
            (gid,)
        )
        row = cur.fetchone()
        con.close()
        return row[0] if row else None

    # ─────────────────────────────
    # INVITES (PERSISTENT)
    # ─────────────────────────────
    def save_inv(self, gid, code, inviter, uses):
        con = self.db()
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO invites VALUES (?,?,?,?)",
            (gid, code, inviter, uses)
        )
        con.commit()
        con.close()

    def load_invites_from_db(self, gid):
        con = self.db()
        cur = con.cursor()
        cur.execute(
            "SELECT code, uses, inviter_id FROM invites WHERE guild_id=?",
            (gid,)
        )
        rows = cur.fetchall()
        con.close()

        cache = {}
        for code, uses, inviter in rows:
            cache[code] = (uses, inviter)
        return cache

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
            e.set_author(name=user.name, icon_url=user.display_avatar.url)
        else:
            e.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url
            )
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
    # LOAD INVITES ON STARTUP
    # ─────────────────────────────
    async def _load_invites(self):
        await self.bot.wait_until_ready()

        for g in self.bot.guilds:
            # restore from DB
            cache = self.load_invites_from_db(g.id)

            try:
                invs = await g.invites()
            except:
                continue

            for i in invs:
                inviter = i.inviter.id if i.inviter else None
                cache[i.code] = (i.uses, inviter)
                self.save_inv(g.id, i.code, inviter, i.uses)

            self.inv_cache[g.id] = cache

    # ─────────────────────────────
    # SLASH COMMANDS
    # ─────────────────────────────
    @app_commands.command(name="logs", description="Configure Vikrant logs")
    async def logs(
        self,
        inter: discord.Interaction,
        action: str,
        channel: discord.TextChannel = None
    ):
        action = action.lower()

        if action == "set":
            if not channel:
                return await inter.response.send_message(
                    "Provide a channel.",
                    ephemeral=True
                )
            self.set_log(inter.guild.id, channel.id)
            return await inter.response.send_message(
                f"Logging → {channel.mention}",
                ephemeral=True
            )

        if action == "show":
            cid = self.get_log(inter.guild.id)
            return await inter.response.send_message(
                f"Log channel: <#{cid}>" if cid else "No log channel set.",
                ephemeral=True
            )

        if action == "disable":
            self.set_log(inter.guild.id, None)
            return await inter.response.send_message(
                "Logging disabled.",
                ephemeral=True
            )

        await inter.response.send_message("Invalid option.", ephemeral=True)

    # ─────────────────────────────
    # EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, m):
        g = m.guild

        try:
            new_invites = await g.invites()
        except:
            new_invites = []

        old = self.inv_cache.get(g.id)
        used = None

        if old:
            for inv in new_invites:
                if inv.code in old and inv.uses > old[inv.code][0]:
                    used = inv
                    break

        # update cache
        cache = {}
        for inv in new_invites:
            inviter = inv.inviter.id if inv.inviter else None
            cache[inv.code] = (inv.uses, inviter)
            self.save_inv(g.id, inv.code, inviter, inv.uses)

        self.inv_cache[g.id] = cache

        e = self.embed("Member Joined", OK, m)
        e.add_field(name="User", value=m.mention, inline=False)

        if used:
            e.add_field(
                name="Invited By",
                value=used.inviter.mention if used.inviter else "Unknown",
                inline=False
            )
            e.add_field(
                name="Invite",
                value=f"`{used.code}`",
                inline=False
            )
        else:
            e.add_field(
                name="Invite",
                value="Unknown (bot restart / vanity)",
                inline=False
            )

        await self.send(g, e)

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
    async def on_message_edit(self, b, a):
        if not b.guild or b.author.bot:
            return
        if b.content == a.content:
            return

        e = self.embed("Message Edited", WARN, b.author)
        e.add_field(name="Channel", value=b.channel.mention, inline=False)
        e.add_field(name="Before", value=b.content[:300], inline=False)
        e.add_field(name="After", value=a.content[:300], inline=False)

        await self.send(b.guild, e)

    @commands.Cog.listener()
    async def on_member_update(self, b, a):
        if b.nick != a.nick:
            actor = None
            async for entry in a.guild.audit_logs(
                action=discord.AuditLogAction.member_update,
                limit=5
            ):
                if entry.target.id == a.id:
                    actor = entry.user
                    break

            e = self.embed("Nickname Changed", WARN, a)
            e.add_field(name="User", value=a.mention, inline=False)
            e.add_field(
                name="Changed By",
                value=actor.mention if actor else "Unknown",
                inline=False
            )
            e.add_field(name="Before", value=b.nick or b.name, inline=True)
            e.add_field(name="After", value=a.nick or a.name, inline=True)
            await self.send(a.guild, e)

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

        e = self.embed("Voice Move", NAVY, m)
        e.add_field(name="User", value=m.mention, inline=False)
        e.add_field(
            name="Moved By",
            value=actor.mention if actor else "Self",
            inline=False
        )
        e.add_field(name="From", value=b.channel.name if b.channel else "None", inline=True)
        e.add_field(name="To", value=a.channel.name if a.channel else "None", inline=True)

        await self.send(m.guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))