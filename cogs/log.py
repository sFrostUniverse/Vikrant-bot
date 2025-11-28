import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime, timezone

DB = "logging.db"

# compact Vikrant colors
NAVY = discord.Color.from_rgb(0, 31, 63)
GREY = discord.Color.from_rgb(108, 122, 137)
OK   = discord.Color.from_rgb(46, 204, 113)
WARN = discord.Color.from_rgb(255, 153, 51)
ALRT = discord.Color.from_rgb(192, 57, 43)


def utc_now():
    return datetime.now(timezone.utc)


class Logs(commands.Cog):
    """Vikrant Compact Logging System"""

    def __init__(self, bot):
        self.bot = bot
        self._db_init()
        self.inv_cache = {}
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
        cur.execute("""
        INSERT OR REPLACE INTO invites VALUES (?,?,?,?)
        """, (gid, code, inviter, uses))
        con.commit()
        con.close()

    def count_inv(self, gid, uid):
        con = self.db()
        cur = con.cursor()
        cur.execute("""
        SELECT SUM(uses) FROM invites WHERE guild_id=? AND inviter_id=?
        """, (gid, uid))
        row = cur.fetchone()
        con.close()
        return row[0] if row and row[0] else 0

    def top_invites(self, gid):
        con = self.db()
        cur = con.cursor()
        cur.execute("""
        SELECT inviter_id, SUM(uses) AS t
        FROM invites
        WHERE guild_id=? AND inviter_id IS NOT NULL
        GROUP BY inviter_id
        ORDER BY t DESC
        LIMIT 10
        """, (gid,))
        rows = cur.fetchall()
        con.close()
        return rows

    # ─────────────────────────────
    # EMBED MAKER (DINO STYLE)
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
            e.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)

        e.set_footer(text="Vikrant Logs")
        return e

    async def send(self, guild, embed):
        ch = self.get_log(guild.id)
        if ch:
            c = guild.get_channel(ch)
            if c:
                try:
                    await c.send(embed=embed)
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
    @app_commands.command(name="logs", description="Configure Vikrant logs")
    async def logs(self, inter, action: str, channel: discord.TextChannel = None):
        action = action.lower()

        if action == "set":
            if not channel:
                return await inter.response.send_message("Provide a channel.", ephemeral=True)
            self.set_log(inter.guild.id, channel.id)
            return await inter.response.send_message(f"Logging → {channel.mention}", ephemeral=True)

        if action == "show":
            cid = self.get_log(inter.guild.id)
            return await inter.response.send_message(
                f"Log channel: <#{cid}>" if cid else "No log channel set.",
                ephemeral=True
            )

        if action == "disable":
            self.set_log(inter.guild.id, None)
            return await inter.response.send_message("Disabled.", ephemeral=True)

        await inter.response.send_message("Invalid option.", ephemeral=True)

    @app_commands.command(name="logs_test")
    async def logs_test(self, inter):
        e = self.embed("Test", OK, inter.user)
        e.add_field(name="Status", value="Working", inline=False)
        await self.send(inter.guild, e)
        await inter.response.send_message("Sent.", ephemeral=True)

    # ─────────────────────────────
    # EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, m):

        g = m.guild
        try:
            new = await g.invites()
        except:
            new = []

        old = self.inv_cache.get(g.id, {})
        used = None

        for inv in new:
            if inv.code in old and inv.uses > old[inv.code][0]:
                used = inv
                break

        cache = {}
        for inv in new:
            inviter = inv.inviter.id if inv.inviter else None
            cache[inv.code] = (inv.uses, inviter)
            self.save_inv(g.id, inv.code, inviter, inv.uses)

        self.inv_cache[g.id] = cache

        e = self.embed("Member Joined", OK, m)
        e.add_field(name="User", value=m.mention, inline=False)

        if used:
            e.add_field(name="Invited By", value=used.inviter.mention, inline=False)
            e.add_field(name="Code", value=f"`{used.code}` ({old[used.code][0]} → {used.uses})", inline=False)

        await self.send(g, e)

    @commands.Cog.listener()
    async def on_member_remove(self, m):
        e = self.embed("Member Left", WARN, m)
        e.add_field(name="User", value=m.mention, inline=False)
        await self.send(m.guild, e)

    @commands.Cog.listener()
    async def on_message_delete(self, msg):

        if not msg.guild or msg.author.bot:
            return

        e = self.embed("Message Deleted", ALRT, msg.author)
        e.add_field(name="User", value=msg.author.mention, inline=False)
        e.add_field(name="Channel", value=msg.channel.mention, inline=False)

        if msg.content:
            e.add_field(name="Content", value=msg.content[:300], inline=False)

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
    async def on_guild_channel_create(self, ch):
        e = self.embed("Channel Created", OK)
        e.add_field(name="Channel", value=ch.mention, inline=False)
        await self.send(ch.guild, e)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, ch):
        e = self.embed("Channel Deleted", ALRT)
        e.add_field(name="Channel", value=f"#{ch.name}", inline=False)
        await self.send(ch.guild, e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, m, b, a):

        g = m.guild

        if not b.channel and a.channel:
            e = self.embed("Voice Join", OK, m)
            e.add_field(name="Channel", value=a.channel.name, inline=False)
            return await self.send(g, e)

        if b.channel and not a.channel:
            e = self.embed("Voice Leave", WARN, m)
            e.add_field(name="Channel", value=b.channel.name, inline=False)
            return await self.send(g, e)

        if b.channel != a.channel:
            e = self.embed("Voice Move", NAVY, m)
            e.add_field(name="From", value=b.channel.name, inline=True)
            e.add_field(name="To", value=a.channel.name, inline=True)
            return await self.send(g, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
