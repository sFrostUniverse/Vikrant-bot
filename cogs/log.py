import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from typing import Optional

CONFIG_FILE = "data/config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_log_channel_id(guild_id: int) -> Optional[int]:
    data = load_config()
    guild_data = data.get(str(guild_id))
    if not guild_data:
        return None
    return guild_data.get("log_channel_id")


def now():
    return datetime.utcnow()


class Logs(commands.Cog):
    """Clean Dyno-style logging"""

    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}
        bot.loop.create_task(self.cache_invites())

    # ─────────────────────────────
    # UTIL
    # ─────────────────────────────
    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        channel_id = get_log_channel_id(guild.id)
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    def base_embed(self, title: str, color: discord.Color):
        e = discord.Embed(
            title=title,
            color=color,
            timestamp=now()
        )
        e.set_footer(text="Vikrant Logs")
        return e

    # ─────────────────────────────
    # INVITE CACHE
    # ─────────────────────────────
    async def cache_invites(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = invites
            except discord.Forbidden:
                self.invite_cache[guild.id] = []

    # ─────────────────────────────
    # EVENTS
    # ─────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        inviter = None
        used_code = None

        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            new_invites = []

        old_invites = self.invite_cache.get(guild.id, [])

        for old in old_invites:
            for new in new_invites:
                if old.code == new.code and new.uses > old.uses:
                    inviter = new.inviter
                    used_code = new.code
                    break

        self.invite_cache[guild.id] = new_invites

        e = self.base_embed("Member Joined", discord.Color.green())
        e.add_field(name="User", value=f"{member} ({member.id})", inline=False)

        if inviter:
            e.add_field(name="Invited By", value=f"{inviter} ({inviter.id})", inline=False)
            e.add_field(name="Invite Code", value=used_code, inline=False)
        else:
            e.add_field(name="Invite", value="Unknown / Vanity / Missing Permission", inline=False)

        await self.send_log(guild, e)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        e = self.base_embed("Member Left", discord.Color.orange())
        e.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        await self.send_log(member.guild, e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        e = self.base_embed("Message Deleted", discord.Color.red())
        e.add_field(name="User", value=message.author.mention, inline=False)
        e.add_field(name="Channel", value=message.channel.mention, inline=False)

        if message.content:
            e.add_field(name="Content", value=message.content[:500], inline=False)

        if message.attachments:
            for a in message.attachments:
                e.add_field(name="Attachment", value=a.url, inline=False)

        await self.send_log(message.guild, e)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return

        e = self.base_embed("Message Edited", discord.Color.gold())
        e.add_field(name="User", value=before.author.mention, inline=False)
        e.add_field(name="Channel", value=before.channel.mention, inline=False)
        e.add_field(name="Before", value=before.content[:300], inline=False)
        e.add_field(name="After", value=after.content[:300], inline=False)

        await self.send_log(before.guild, e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Nickname change
        if before.nick != after.nick:
            e = self.base_embed("Nickname Changed", discord.Color.blurple())
            e.add_field(name="User", value=after.mention, inline=False)
            e.add_field(name="Before", value=before.nick or before.name, inline=True)
            e.add_field(name="After", value=after.nick or after.name, inline=True)
            await self.send_log(after.guild, e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return

        e = self.base_embed("Voice State Update", discord.Color.blue())
        e.add_field(name="User", value=member.mention, inline=False)
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

        await self.send_log(member.guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
