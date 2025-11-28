import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime, timezone

DB_PATH = "logging.db"


# --------- VIKRANT THEME COLORS (ship hull + navy) ----------
VIKRANT_HULL = discord.Color.from_rgb(108, 122, 137)   # steel grey
VIKRANT_NAVY = discord.Color.from_rgb(0, 31, 63)       # deep navy blue
VIKRANT_ALERT = discord.Color.from_rgb(192, 57, 43)    # red alert
VIKRANT_WARN = discord.Color.from_rgb(255, 153, 51)    # saffron-like
VIKRANT_OK = discord.Color.from_rgb(41, 128, 185)      # blue status


def now_utc():
    # Use aware datetime for timestamps
    return datetime.now(timezone.utc)


def ts_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Logs(commands.Cog):
    """INS Vikrant - Naval Surveillance Logging System"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._init_db()
        self.invite_cache = {}  # guild_id -> {code: (uses, inviter_id)}
        # Build invite cache after bot is ready
        self.bot.loop.create_task(self._build_invite_cache())

    # ---------------------- DB INIT & HELPERS ----------------------

    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _init_db(self):
        con = self._connect()
        cur = con.cursor()
        # logging channel
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                guild_id   INTEGER PRIMARY KEY,
                channel_id INTEGER
            )
            """
        )
        # invites
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS invites (
                guild_id   INTEGER,
                code       TEXT,
                inviter_id INTEGER,
                uses       INTEGER,
                PRIMARY KEY (guild_id, code)
            )
            """
        )
        con.commit()
        con.close()

    def db_set_log_channel(self, guild_id: int, channel_id: int):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO logs (guild_id, channel_id) VALUES (?, ?)",
            (guild_id, channel_id),
        )
        con.commit()
        con.close()

    def db_get_log_channel(self, guild_id: int) -> int | None:
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT channel_id FROM logs WHERE guild_id = ?", (guild_id,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else None

    def db_clear_log_channel(self, guild_id: int):
        con = self._connect()
        cur = con.cursor()
        cur.execute("DELETE FROM logs WHERE guild_id = ?", (guild_id,))
        con.commit()
        con.close()

    def db_save_invite(self, guild_id: int, code: str, inviter_id: int | None, uses: int):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO invites (guild_id, code, inviter_id, uses)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, code, inviter_id, uses),
        )
        con.commit()
        con.close()

    def db_get_invites_for_guild(self, guild_id: int) -> dict:
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT code, inviter_id, uses FROM invites WHERE guild_id = ?",
            (guild_id,),
        )
        rows = cur.fetchall()
        con.close()
        return {code: (inviter_id, uses) for code, inviter_id, uses in rows}

    def db_get_invite_stats_for_user(self, guild_id: int, user_id: int) -> int:
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(uses) FROM invites WHERE guild_id = ? AND inviter_id = ?",
            (guild_id, user_id),
        )
        row = cur.fetchone()
        con.close()
        return row[0] if row and row[0] is not None else 0

    def db_get_invites_top(self, guild_id: int, limit: int = 10):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            """
            SELECT inviter_id, SUM(uses) AS total_uses
            FROM invites
            WHERE guild_id = ?
            AND inviter_id IS NOT NULL
            GROUP BY inviter_id
            ORDER BY total_uses DESC
            LIMIT ?
            """,
            (guild_id, limit),
        )
        rows = cur.fetchall()
        con.close()
        return rows  # list of (inviter_id, total_uses)

    # ---------------------- CORE LOGGING UTIL ----------------------

    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        channel_id = self.db_get_log_channel(guild.id)
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        try:
            await channel.send(embed=embed)
        except Exception:
            # avoid crashing on permission issues etc.
            pass

    def make_embed(
        self,
        title_suffix: str,
        description: str | None = None,
        color: discord.Color = VIKRANT_HULL,
    ) -> discord.Embed:
        title = f"⛨ INS VIKRANT // {title_suffix}"
        embed = discord.Embed(
            title=title,
            description=description or "",
            color=color,
            timestamp=now_utc(),
        )
        # Author icon: Vikrant bot itself (if available)
        if self.bot.user:
            embed.set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.display_avatar.url,
            )
        embed.set_footer(text="INS Vikrant • Naval Surveillance Online")
        return embed

    # ---------------------- INVITE CACHE SETUP ----------------------

    async def _build_invite_cache(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
            except discord.Forbidden:
                continue

            cache = {}
            for inv in invites:
                inviter_id = inv.inviter.id if inv.inviter else None
                cache[inv.code] = (inv.uses, inviter_id)
                self.db_save_invite(guild.id, inv.code, inviter_id, inv.uses)

            self.invite_cache[guild.id] = cache

    # ---------------------- SLASH COMMANDS ----------------------

    @app_commands.command(
        name="logs",
        description="Configure Vikrant logging channel (set / show / disable).",
    )
    @app_commands.describe(
        action="set / show / disable",
        channel="Channel to log events into (for 'set')",
    )
    async def logs_command(
        self,
        interaction: discord.Interaction,
        action: str,
        channel: discord.TextChannel | None = None,
    ):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message(
                "❌ You need **Manage Server** permission to configure logs.",
                ephemeral=True,
            )

        action = action.lower()
        guild = interaction.guild

        if action == "set":
            if channel is None:
                return await interaction.response.send_message(
                    "❌ Please specify a channel.",
                    ephemeral=True,
                )
            self.db_set_log_channel(guild.id, channel.id)
            return await interaction.response.send_message(
                f"✅ Logging channel set to {channel.mention}",
                ephemeral=True,
            )

        elif action == "show":
            ch_id = self.db_get_log_channel(guild.id)
            if ch_id:
                return await interaction.response.send_message(
                    f"📡 Current logging channel: <#{ch_id}>",
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                "⚠ No logging channel set.",
                ephemeral=True,
            )

        elif action == "disable":
            self.db_clear_log_channel(guild.id)
            return await interaction.response.send_message(
                "🛑 Logging disabled.",
                ephemeral=True,
            )

        else:
            return await interaction.response.send_message(
                "❌ Invalid action. Use: `set`, `show`, or `disable`.",
                ephemeral=True,
            )

    @app_commands.command(
        name="logs_test",
        description="Send a test Vikrant log to the configured log channel.",
    )
    async def logs_test(self, interaction: discord.Interaction):
        guild = interaction.guild
        ch_id = self.db_get_log_channel(guild.id)
        if not ch_id:
            return await interaction.response.send_message(
                "⚠ No log channel set. Use `/logs set #channel` first.",
                ephemeral=True,
            )

        embed = self.make_embed(
            "SYSTEM TEST",
            description="📡 Vikrant surveillance systems are online.\n"
            f"Test initiated by {interaction.user.mention}",
            color=VIKRANT_OK,
        )
        await self.send_log(guild, embed)
        await interaction.response.send_message(
            "✅ Test log sent to configured channel.",
            ephemeral=True,
        )

    @app_commands.command(
        name="invites",
        description="Show how many members a user has invited.",
    )
    async def invites_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None,
    ):
        guild = interaction.guild
        user = user or interaction.user
        total = self.db_get_invite_stats_for_user(guild.id, user.id)

        embed = self.make_embed(
            "INVITE STATS",
            color=VIKRANT_NAVY,
        )
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Total Invited", value=str(total), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="invites_top",
        description="Show top inviters in this server.",
    )
    async def invites_top(self, interaction: discord.Interaction):
        guild = interaction.guild
        rows = self.db_get_invites_top(guild.id, limit=10)

        embed = self.make_embed(
            "INVITE LEADERBOARD",
            color=VIKRANT_NAVY,
        )

        if not rows:
            embed.description = "No invite data tracked yet."
        else:
            lines = []
            for idx, (user_id, total) in enumerate(rows, start=1):
                member = guild.get_member(user_id)
                name = member.mention if member else f"`{user_id}`"
                lines.append(f"**#{idx}** {name} — **{total}** joins")
            embed.description = "\n".join(lines)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------------- MEMBER JOIN / LEAVE ----------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        # Fetch invites again to compare
        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            new_invites = []

        old_invites = self.invite_cache.get(guild.id, {})
        used_invite = None

        for inv in new_invites:
            old_data = old_invites.get(inv.code)
            if old_data and inv.uses > old_data[0]:
                used_invite = inv
                break

        # Update cache & DB
        cache = {}
        for inv in new_invites:
            inviter_id = inv.inviter.id if inv.inviter else None
            cache[inv.code] = (inv.uses, inviter_id)
            self.db_save_invite(guild.id, inv.code, inviter_id, inv.uses)
        self.invite_cache[guild.id] = cache

        embed = self.make_embed(
            "MEMBER JOINED",
            color=VIKRANT_OK,
        )
        embed.add_field("User", f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(
            "Account Created",
            member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False,
        )

        if used_invite:
            old_uses = old_invites.get(used_invite.code, (used_invite.uses - 1,))[0]
            embed.add_field(
                "Invited By",
                f"{used_invite.inviter.mention} (`{used_invite.inviter.id}`)",
                inline=False,
            )
            embed.add_field(
                "Invite Code",
                f"`{used_invite.code}` — uses: **{old_uses} → {used_invite.uses}**",
                inline=False,
            )
        else:
            embed.add_field(
                "Invite Info",
                "Could not determine invite (vanity link, expired, or insufficient perms).",
                inline=False,
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild

        # Try to see if this was a kick using audit logs
        action_str = "MEMBER LEFT"
        color = VIKRANT_WARN
        mod_text = None

        try:
            async for entry in guild.audit_logs(
                limit=5, action=discord.AuditLogAction.kick
            ):
                if entry.target.id == member.id:
                    action_str = "MEMBER KICKED"
                    color = VIKRANT_ALERT
                    mod_text = f"{entry.user.mention} (`{entry.user.id}`)"
                    break
        except discord.Forbidden:
            pass

        embed = self.make_embed(action_str, color=color)
        embed.add_field("User", f"{member.mention} (`{member.id}`)", inline=False)
        if mod_text:
            embed.add_field("By Moderator", mod_text, inline=False)

        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(guild, embed)

    # ---------------------- BAN / UNBAN ----------------------

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        moderator = None
        reason = None
        try:
            async for entry in guild.audit_logs(
                limit=5, action=discord.AuditLogAction.ban
            ):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            pass

        embed = self.make_embed("MEMBER BANNED", color=VIKRANT_ALERT)
        embed.add_field("User", f"{user.mention} (`{user.id}`)", inline=False)
        if moderator:
            embed.add_field(
                "By Moderator",
                f"{moderator.mention} (`{moderator.id}`)",
                inline=False,
            )
        if reason:
            embed.add_field("Reason", reason, inline=False)

        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        moderator = None
        try:
            async for entry in guild.audit_logs(
                limit=5, action=discord.AuditLogAction.unban
            ):
                if entry.target.id == user.id:
                    moderator = entry.user
                    break
        except discord.Forbidden:
            pass

        embed = self.make_embed("MEMBER UNBANNED", color=VIKRANT_OK)
        embed.add_field("User", f"{user.mention} (`{user.id}`)", inline=False)
        if moderator:
            embed.add_field(
                "By Moderator",
                f"{moderator.mention} (`{moderator.id}`)",
                inline=False,
            )
        embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_log(guild, embed)

    # ---------------------- MESSAGE LOGS ----------------------

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        # Try to see if a mod deleted it
        deleter = None
        try:
            async for entry in message.guild.audit_logs(
                limit=5, action=discord.AuditLogAction.message_delete
            ):
                if (
                    entry.target.id == message.author.id
                    and entry.extra.channel.id == message.channel.id
                ):
                    deleter = entry.user
                    break
        except discord.Forbidden:
            pass

        embed = self.make_embed("MESSAGE DELETED", color=VIKRANT_ALERT)
        embed.add_field(
            "Author",
            f"{message.author.mention} (`{message.author.id}`)",
            inline=False,
        )
        embed.add_field("Channel", message.channel.mention, inline=False)

        if message.content:
            trimmed = message.content[:1000]
            embed.add_field("Content", trimmed, inline=False)

        if message.attachments:
            files_list = "\n".join(att.url for att in message.attachments)
            embed.add_field("Attachments", files_list[:1000], inline=False)

        if deleter:
            embed.add_field(
                "Deleted By",
                f"{deleter.mention} (`{deleter.id}`)",
                inline=False,
            )

        embed.set_thumbnail(url=message.author.display_avatar.url)
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        messages = list(messages)
        if not messages:
            return
        guild = messages[0].guild
        channel = messages[0].channel

        embed = self.make_embed("BULK MESSAGE DELETE", color=VIKRANT_ALERT)
        embed.add_field("Channel", channel.mention, inline=False)
        embed.add_field("Messages Deleted", str(len(messages)), inline=False)

        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return

        embed = self.make_embed("MESSAGE EDITED", color=VIKRANT_WARN)
        embed.add_field(
            "Author",
            f"{before.author.mention} (`{before.author.id}`)",
            inline=False,
        )
        embed.add_field("Channel", before.channel.mention, inline=False)
        embed.add_field(
            "Before",
            before.content[:1000] or "*None*",
            inline=False,
        )
        embed.add_field(
            "After",
            after.content[:1000] or "*None*",
            inline=False,
        )
        embed.set_thumbnail(url=before.author.display_avatar.url)
        await self.send_log(before.guild, embed)

    # ---------------------- VOICE LOGS ----------------------

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild

        # Join VC
        if before.channel is None and after.channel is not None:
            embed = self.make_embed("VOICE JOIN", color=VIKRANT_OK)
            embed.description = (
                f"🎧 {member.mention} joined voice channel "
                f"**{after.channel.name}**"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            return await self.send_log(guild, embed)

        # Leave VC
        if before.channel is not None and after.channel is None:
            embed = self.make_embed("VOICE LEAVE", color=VIKRANT_WARN)
            embed.description = (
                f"🎧 {member.mention} left voice channel "
                f"**{before.channel.name}**"
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            return await self.send_log(guild, embed)

        # Channel move
        if before.channel != after.channel:
            mover = None
            try:
                async for entry in guild.audit_logs(
                    limit=5, action=discord.AuditLogAction.member_move
                ):
                    if entry.target.id == member.id:
                        mover = entry.user
                        break
            except discord.Forbidden:
                pass

            embed = self.make_embed("VOICE MOVE", color=VIKRANT_NAVY)
            if mover:
                embed.description = (
                    f"🎧 {mover.mention} moved {member.mention}\n"
                    f"🔊 **{before.channel.name}** → **{after.channel.name}**"
                )
            else:
                embed.description = (
                    f"🎧 {member.mention} switched voice channels\n"
                    f"🔊 **{before.channel.name}** → **{after.channel.name}**"
                )
            embed.set_thumbnail(url=member.display_avatar.url)
            return await self.send_log(guild, embed)

        # Mute / deaf / etc.
        if before.self_mute != after.self_mute:
            state = "muted" if after.self_mute else "unmuted"
            embed = self.make_embed("VOICE MUTE", color=VIKRANT_HULL)
            embed.description = f"🎧 {member.mention} **self-{state}** in **{after.channel.name}**"
            return await self.send_log(guild, embed)

        if before.self_deaf != after.self_deaf:
            state = "deafened" if after.self_deaf else "undeafened"
            embed = self.make_embed("VOICE DEAF", color=VIKRANT_HULL)
            embed.description = f"🎧 {member.mention} **self-{state}** in **{after.channel.name}**"
            return await self.send_log(guild, embed)

        if before.mute != after.mute:
            state = "server-muted" if after.mute else "server-unmuted"
            embed = self.make_embed("VOICE SERVER MUTE", color=VIKRANT_HULL)
            embed.description = f"🎧 {member.mention} was **{state}** in **{after.channel.name}**"
            return await self.send_log(guild, embed)

        if before.deaf != after.deaf:
            state = "server-deafened" if after.deaf else "server-undeafened"
            embed = self.make_embed("VOICE SERVER DEAF", color=VIKRANT_HULL)
            embed.description = f"🎧 {member.mention} was **{state}** in **{after.channel.name}**"
            return await self.send_log(guild, embed)

    # ---------------------- ROLE & MEMBER UPDATE LOGS ----------------------

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):
        guild = before.guild

        # Nickname change
        if before.nick != after.nick:
            embed = self.make_embed("NICKNAME CHANGE", color=VIKRANT_HULL)
            embed.add_field(
                "User",
                f"{before.mention} (`{before.id}`)",
                inline=False,
            )
            embed.add_field(
                "Before",
                before.nick or before.name,
                inline=True,
            )
            embed.add_field(
                "After",
                after.nick or after.name,
                inline=True,
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await self.send_log(guild, embed)

        # Role changes
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        gained = after_roles - before_roles
        lost = before_roles - after_roles

        if gained or lost:
            embed = self.make_embed("ROLE UPDATE", color=VIKRANT_NAVY)
            embed.add_field(
                "User",
                f"{after.mention} (`{after.id}`)",
                inline=False,
            )
            if gained:
                embed.add_field(
                    "Roles Added",
                    ", ".join(r.mention for r in gained if r.name != "@everyone")
                    or "None",
                    inline=False,
                )
            if lost:
                embed.add_field(
                    "Roles Removed",
                    ", ".join(r.mention for r in lost if r.name != "@everyone")
                    or "None",
                    inline=False,
                )
            embed.set_thumbnail(url=after.display_avatar.url)
            await self.send_log(guild, embed)

    # ---------------------- CHANNEL LOGS ----------------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        embed = self.make_embed("CHANNEL CREATED", color=VIKRANT_OK)
        embed.add_field("Channel", channel.mention if hasattr(channel, "mention") else channel.name, inline=False)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        embed = self.make_embed("CHANNEL DELETED", color=VIKRANT_ALERT)
        embed.add_field("Channel", f"#{channel.name}", inline=False)
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ):
        guild = after.guild
        if before.name != after.name:
            embed = self.make_embed("CHANNEL RENAMED", color=VIKRANT_HULL)
            embed.add_field("Before", f"#{before.name}", inline=True)
            embed.add_field("After", f"#{after.name}", inline=True)
            await self.send_log(guild, embed)

    # ---------------------- ROLE LOGS ----------------------

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = self.make_embed("ROLE CREATED", color=VIKRANT_OK)
        embed.add_field("Role", role.mention, inline=False)
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = self.make_embed("ROLE DELETED", color=VIKRANT_ALERT)
        embed.add_field("Role", role.name, inline=False)
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        guild = after.guild
        if before.name != after.name:
            embed = self.make_embed("ROLE RENAMED", color=VIKRANT_HULL)
            embed.add_field("Before", before.name, inline=True)
            embed.add_field("After", after.name, inline=True)
            await self.send_log(guild, embed)

    # ---------------------- EMOJI & SERVER LOGS (BASIC) ----------------------

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        before_set = {e.id: e for e in before}
        after_set = {e.id: e for e in after}

        # Added
        for eid, emoji in after_set.items():
            if eid not in before_set:
                embed = self.make_embed("EMOJI ADDED", color=VIKRANT_OK)
                embed.add_field("Emoji", str(emoji), inline=False)
                await self.send_log(guild, embed)

        # Removed
        for eid, emoji in before_set.items():
            if eid not in after_set:
                embed = self.make_embed("EMOJI REMOVED", color=VIKRANT_ALERT)
                embed.add_field("Emoji", str(emoji), inline=False)
                await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        changes = []

        if before.name != after.name:
            changes.append(("Name", before.name, after.name))
        if before.icon != after.icon:
            changes.append(("Icon", "Changed", "Changed"))
        if before.banner != after.banner:
            changes.append(("Banner", "Changed", "Changed"))
        if before.vanity_url_code != after.vanity_url_code:
            changes.append(("Vanity URL", before.vanity_url_code, after.vanity_url_code))

        if not changes:
            return

        embed = self.make_embed("SERVER UPDATED", color=VIKRANT_HULL)
        for field, old, new in changes:
            embed.add_field(
                field,
                f"**Before:** {old or 'None'}\n**After:** {new or 'None'}",
                inline=False,
            )
        await self.send_log(after, embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
