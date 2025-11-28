import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime, timezone

DB_PATH = "logging.db"

# ----------- INS VIKRANT THEME COLORS -------------
VIKRANT_HULL = discord.Color.from_rgb(108, 122, 137)   # steel grey
VIKRANT_NAVY = discord.Color.from_rgb(0, 31, 63)       # deep navy blue
VIKRANT_ALERT = discord.Color.from_rgb(192, 57, 43)    # red alert
VIKRANT_WARN = discord.Color.from_rgb(255, 153, 51)    # saffron
VIKRANT_OK = discord.Color.from_rgb(41, 128, 185)      # ocean blue

def now_utc():
    return datetime.now(timezone.utc)

def ts_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class Logs(commands.Cog):
    """INS Vikrant – Naval Surveillance Logging System"""

    def __init__(self, bot):
        self.bot = bot
        self._db_init()
        self.invite_cache = {}
        self.bot.loop.create_task(self._build_invite_cache())

    # ---------------- DB ----------------
    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _db_init(self):
        con = self._connect()
        cur = con.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS invites (
                guild_id INTEGER,
                code TEXT,
                inviter_id INTEGER,
                uses INTEGER,
                PRIMARY KEY (guild_id, code)
            )
        """)

        con.commit()
        con.close()

    def db_set_log_channel(self, guild_id, channel_id):
        con = self._connect()
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO logs VALUES (?,?)", (guild_id, channel_id))
        con.commit()
        con.close()

    def db_get_log_channel(self, guild_id):
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT channel_id FROM logs WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else None

    def db_clear_log_channel(self, guild_id):
        con = self._connect()
        cur = con.cursor()
        cur.execute("DELETE FROM logs WHERE guild_id=?", (guild_id,))
        con.commit()
        con.close()

    def db_save_invite(self, guild_id, code, inviter_id, uses):
        con = self._connect()
        cur = con.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO invites VALUES (?, ?, ?, ?)
        """, (guild_id, code, inviter_id, uses))
        con.commit()
        con.close()

    def db_invites_for_guild(self, guild_id):
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT code, inviter_id, uses FROM invites WHERE guild_id=?", (guild_id,))
        rows = cur.fetchall()
        con.close()
        return {code: (inviter_id, uses) for code, inviter_id, uses in rows}

    def db_invites_count_for_user(self, guild_id, user_id):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(uses) FROM invites WHERE guild_id=? AND inviter_id=?",
            (guild_id, user_id)
        )
        row = cur.fetchone()
        con.close()
        return row[0] if row and row[0] else 0

    def db_invites_top(self, guild_id, limit=10):
        con = self._connect()
        cur = con.cursor()
        cur.execute("""
            SELECT inviter_id, SUM(uses) AS total
            FROM invites
            WHERE guild_id=? AND inviter_id IS NOT NULL
            GROUP BY inviter_id
            ORDER BY total DESC
            LIMIT ?
        """, (guild_id, limit))
        rows = cur.fetchall()
        con.close()
        return rows

    # ---------------- UTILS ---------------
    async def send_log(self, guild, embed):
        channel_id = self.db_get_log_channel(guild.id)
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

    def make_embed(self, title, desc="", color=VIKRANT_HULL):
        embed = discord.Embed(
            title=f"⛨ INS VIKRANT // {title}",
            description=desc,
            color=color,
            timestamp=now_utc()
        )
        if self.bot.user:
            embed.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url
            )
        embed.set_footer(text="INS Vikrant • Naval Surveillance Online")
        return embed

    # ------------- INVITE CACHE ----------------
    async def _build_invite_cache(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
            except:
                continue

            cache = {}
            for inv in invites:
                inviter = inv.inviter.id if inv.inviter else None
                cache[inv.code] = (inv.uses, inviter)
                self.db_save_invite(guild.id, inv.code, inviter, inv.uses)

            self.invite_cache[guild.id] = cache

    # ---------------- SLASH COMMANDS ----------------

    @app_commands.command(name="logs", description="Configure Vikrant log channel")
    async def logs_cmd(self, interaction: discord.Interaction, action: str, channel: discord.TextChannel = None):
        action = action.lower()
        guild = interaction.guild

        if action == "set":
            if channel is None:
                return await interaction.response.send_message("❌ Provide a channel.", ephemeral=True)
            self.db_set_log_channel(guild.id, channel.id)
            return await interaction.response.send_message(f"✅ Log channel set to {channel.mention}", ephemeral=True)

        if action == "show":
            ch = self.db_get_log_channel(guild.id)
            if ch:
                return await interaction.response.send_message(f"📡 Logs → <#{ch}>", ephemeral=True)
            return await interaction.response.send_message("⚠ No log channel configured.", ephemeral=True)

        if action == "disable":
            self.db_clear_log_channel(guild.id)
            return await interaction.response.send_message("🛑 Logging disabled.", ephemeral=True)

        return await interaction.response.send_message("❌ Invalid. Use: set / show / disable", ephemeral=True)

    @app_commands.command(name="logs_test", description="Send a Vikrant test log")
    async def logs_test(self, interaction: discord.Interaction):
        embed = self.make_embed("SYSTEM TEST", "📡 Vikrant surveillance is online.", VIKRANT_OK)
        await self.send_log(interaction.guild, embed)
        await interaction.response.send_message("✅ Sent.", ephemeral=True)

    @app_commands.command(name="invites", description="Check how many users someone invited.")
    async def invites(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        total = self.db_invites_count_for_user(interaction.guild.id, user.id)

        embed = self.make_embed("INVITE STATS", color=VIKRANT_NAVY)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Total Invited", value=str(total), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invites_top", description="Top inviters in the server")
    async def invites_top(self, interaction: discord.Interaction):
        rows = self.db_invites_top(interaction.guild.id)

        embed = self.make_embed("INVITE LEADERBOARD", color=VIKRANT_NAVY)

        if not rows:
            embed.description = "No invite data yet."
        else:
            text = ""
            for i, (uid, total) in enumerate(rows, start=1):
                member = interaction.guild.get_member(uid)
                name = member.mention if member else f"`{uid}`"
                text += f"**#{i}** {name}: **{total}** invites\n"
            embed.description = text

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------- MEMBER JOIN ----------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        try:
            new_invites = await guild.invites()
        except:
            new_invites = []

        old = self.invite_cache.get(guild.id, {})
        used = None

        for inv in new_invites:
            if inv.code in old and inv.uses > old[inv.code][0]:
                used = inv
                break

        cache = {}
        for inv in new_invites:
            inviter = inv.inviter.id if inv.inviter else None
            cache[inv.code] = (inv.uses, inviter)
            self.db_save_invite(guild.id, inv.code, inviter, inv.uses)
        self.invite_cache[guild.id] = cache

        embed = self.make_embed("MEMBER JOINED", color=VIKRANT_OK)
        embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)

        if used:
            old_uses = old[used.code][0]
            embed.add_field(name="Invited By", value=used.inviter.mention, inline=False)
            embed.add_field(name="Invite Code", value=f"`{used.code}`", inline=False)
            embed.add_field(
                name="Invite Uses",
                value=f"{old_uses} → {used.uses}",
                inline=False
            )
        else:
            embed.add_field(
                name="Invite Info",
                value="Could not determine (vanity / expired / missing perms).",
                inline=False
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(guild, embed)

    # ---------------- MEMBER LEAVE ----------------

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        embed = self.make_embed("MEMBER LEFT", color=VIKRANT_WARN)
        embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(guild, embed)

    # ---------------- MESSAGE DELETE ----------------

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return

        embed = self.make_embed("MESSAGE DELETED", color=VIKRANT_ALERT)
        embed.add_field(
            name="Author",
            value=f"{message.author.mention} (`{message.author.id}`)",
            inline=False
        )
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)

        if message.content:
            embed.add_field(name="Content", value=message.content[:1000], inline=False)

        if message.attachments:
            links = "\n".join(a.url for a in message.attachments)
            embed.add_field(name="Attachments", value=links[:1000], inline=False)

        embed.set_thumbnail(url=message.author.display_avatar.url)
        await self.send_log(message.guild, embed)

    # ---------------- MESSAGE EDIT ----------------

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        embed = self.make_embed("MESSAGE EDITED", color=VIKRANT_WARN)
        embed.add_field(name="Author", value=before.author.mention, inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content[:1000] or "*None*", inline=False)
        embed.add_field(name="After", value=after.content[:1000] or "*None*", inline=False)
        embed.set_thumbnail(url=before.author.display_avatar.url)

        await self.send_log(before.guild, embed)

    # ---------------- BULK DELETE ----------------

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
        guild = messages[0].guild
        channel = messages[0].channel

        embed = self.make_embed("BULK DELETE", color=VIKRANT_ALERT)
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Messages Deleted", value=str(len(messages)), inline=False)
        await self.send_log(guild, embed)

    # ---------------- VOICE LOGS ----------------

    @commands.Cog.listener()
    async def on_voice_state_update(self, m, before, after):
        guild = m.guild

        if before.channel is None and after.channel is not None:
            embed = self.make_embed("VOICE JOIN", f"{m.mention} joined **{after.channel.name}**", VIKRANT_OK)
            embed.set_thumbnail(url=m.display_avatar.url)
            return await self.send_log(guild, embed)

        if before.channel and after.channel is None:
            embed = self.make_embed("VOICE LEAVE", f"{m.mention} left **{before.channel.name}**", VIKRANT_WARN)
            embed.set_thumbnail(url=m.display_avatar.url)
            return await self.send_log(guild, embed)

        if before.channel != after.channel:
            embed = self.make_embed("VOICE MOVE", color=VIKRANT_NAVY)
            embed.add_field(
                name="Movement",
                value=f"**{before.channel.name}** → **{after.channel.name}**",
                inline=False
            )
            embed.add_field(name="User", value=m.mention, inline=False)
            embed.set_thumbnail(url=m.display_avatar.url)
            return await self.send_log(guild, embed)

    # ---------------- CHANNEL LOGS ----------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        embed = self.make_embed("CHANNEL CREATED", color=VIKRANT_OK)
        embed.add_field(
            name="Channel",
            value=channel.mention if hasattr(channel, "mention") else channel.name,
            inline=False
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        embed = self.make_embed("CHANNEL DELETED", color=VIKRANT_ALERT)
        embed.add_field(
            name="Channel",
            value=f"#{channel.name}",
            inline=False
        )
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        guild = after.guild
        if before.name != after.name:
            embed = self.make_embed("CHANNEL RENAMED", color=VIKRANT_HULL)
            embed.add_field(name="Before", value=f"#{before.name}", inline=True)
            embed.add_field(name="After", value=f"#{after.name}", inline=True)
            await self.send_log(guild, embed)

    # ---------------- ROLE LOGS ----------------

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = self.make_embed("ROLE CREATED", color=VIKRANT_OK)
        embed.add_field(name="Role", value=role.mention, inline=False)
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = self.make_embed("ROLE DELETED", color=VIKRANT_ALERT)
        embed.add_field(name="Role", value=role.name, inline=False)
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = after.guild
        if before.name != after.name:
            embed = self.make_embed("ROLE NAME CHANGED", color=VIKRANT_HULL)
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            await self.send_log(guild, embed)

    # ---------------- EMOJI LOGS ----------------

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        before_map = {e.id: e for e in before}
        after_map = {e.id: e for e in after}

        for eid, emoji in after_map.items():
            if eid not in before_map:
                embed = self.make_embed("EMOJI ADDED", color=VIKRANT_OK)
                embed.add_field(name="Emoji", value=str(emoji), inline=False)
                await self.send_log(guild, embed)

        for eid, emoji in before_map.items():
            if eid not in after_map:
                embed = self.make_embed("EMOJI REMOVED", color=VIKRANT_ALERT)
                embed.add_field(name="Emoji", value=str(emoji), inline=False)
                await self.send_log(guild, embed)

    # ---------------- GUILD UPDATE ----------------

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(("Name", before.name, after.name))
        if before.icon != after.icon:
            changes.append(("Icon", "Changed", "Changed"))
        if before.banner != after.banner:
            changes.append(("Banner", "Changed", "Changed"))

        if not changes:
            return

        embed = self.make_embed("SERVER UPDATED", color=VIKRANT_HULL)
        for label, old, new in changes:
            embed.add_field(
                name=label,
                value=f"**Before:** {old or 'None'}\n**After:** {new or 'None'}",
                inline=False
            )

        await self.send_log(after, embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
