import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone

CONFIG_FILE = "data/config.json"


# ─────────────────────────────
# CONFIG HELPERS
# ─────────────────────────────
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_log_channel(guild: discord.Guild):
    data = load_config().get(str(guild.id))
    if not data:
        return None
    return guild.get_channel(data.get("log_channel_id"))


# ─────────────────────────────
# LOG COG
# ─────────────────────────────
class Logs(commands.Cog):
    """Dyno-style logging"""

    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}
        bot.loop.create_task(self.cache_invites())

    # ─────────────────────────────
    # UTIL
    # ─────────────────────────────
    async def send_log(self, guild, embed):
        channel = get_log_channel(guild)
        if not channel:
            return
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    def base(self, title, color):
        e = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        e.set_footer(text="Vikrant Logs")
        return e

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
    # MEMBER JOIN (INVITES)
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

        e = self.base("Member Joined", discord.Color.green())
        e.add_field(name="User", value=member.mention, inline=False)

        if inviter:
            e.add_field(name="Invited By", value=inviter.mention, inline=False)
            e.add_field(name="Code", value=code, inline=False)
        else:
            e.add_field(name="Invite", value="Unknown / Vanity / Bot Offline", inline=False)

        await self.send_log(guild, e)

    # ─────────────────────────────
    # MESSAGE DELETE (TEXT + IMAGES)
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.guild or msg.author.bot:
            return

        e = self.base("Message Deleted", discord.Color.red())
        e.add_field(name="User", value=msg.author.mention, inline=False)
        e.add_field(name="Channel", value=msg.channel.mention, inline=False)

        if msg.content:
            e.add_field(name="Content", value=msg.content[:500], inline=False)

        for a in msg.attachments:
            e.add_field(name="Attachment", value=a.url, inline=False)

        await self.send_log(msg.guild, e)

    # ─────────────────────────────
    # MESSAGE EDIT
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        e = self.base("Message Edited", discord.Color.orange())
        e.add_field(name="User", value=before.author.mention, inline=False)
        e.add_field(name="Channel", value=before.channel.mention, inline=False)
        e.add_field(name="Before", value=before.content[:300], inline=False)
        e.add_field(name="After", value=after.content[:300], inline=False)

        await self.send_log(before.guild, e)

    # ─────────────────────────────
    # VOICE EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return

        e = self.base("Voice Activity", discord.Color.blurple())
        e.add_field(name="User", value=member.mention, inline=False)

        if not before.channel:
            e.add_field(name="Action", value=f"Joined **{after.channel.name}**", inline=False)
        elif not after.channel:
            e.add_field(name="Action", value=f"Left **{before.channel.name}**", inline=False)
        else:
            e.add_field(
                name="Action",
                value=f"Switched **{before.channel.name} → {after.channel.name}**",
                inline=False
            )

        await self.send_log(member.guild, e)

    # ─────────────────────────────
    # CHANNEL UPDATE
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append(f"Name changed: **{before.name} → {after.name}**")

        if before.overwrites != after.overwrites:
            changes.append("Permissions updated")

        if not changes:
            return

        e = self.base("Channel Updated", discord.Color.gold())
        e.add_field(name="Channel", value=after.mention, inline=False)
        e.add_field(name="Changes", value="\n".join(changes), inline=False)

        await self.send_log(after.guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
