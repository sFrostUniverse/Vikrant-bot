import discord
from discord.ext import commands
import re, time, json, os

CONFIG_FILE = "data/config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

class LinkSpamProtection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_links = {}

    LINK_REGEX = r"(https?://[^\s]+)"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = load_config().get(str(message.guild.id), {})
        trusted_admins = config.get("trusted_admins", [])
        log_channel_id = config.get("admin_log_channel")

        if message.author.id in trusted_admins:
            return

        urls = re.findall(self.LINK_REGEX, message.content)
        if not urls:
            return

        user_id = message.author.id
        now = time.time()

        for url in urls:
            if user_id not in self.recent_links:
                self.recent_links[user_id] = []
            self.recent_links[user_id].append({
                "url": url,
                "channel": message.channel.id,
                "time": now
            })

            self.recent_links[user_id] = [
                entry for entry in self.recent_links[user_id]
                if now - entry["time"] <= 20
            ]

            channels = {entry["channel"] for entry in self.recent_links[user_id] if entry["url"] == url}
            if len(channels) >= 3:
                try:
                    await message.guild.kick(message.author, reason="Link spamming detected by Vikrant")
                    if log_channel_id:
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel:
                            embed = discord.Embed(
                                title="🚨 Link Spam Detected",
                                description=(
                                    f"User {message.author.mention} was kicked for link spam.\n"
                                    f"**Link:** `{url}`\n"
                                    f"**Channels:** {len(channels)}\n"
                                ),
                                color=discord.Color.red()
                            )
                            embed.set_footer(text="Vikrant • Auto-Protection")
                            await log_channel.send(embed=embed)
                except Exception as e:
                    print(f"Error kicking user: {e}")

                self.recent_links.pop(user_id, None)
                break

async def setup(bot):
    await bot.add_cog(LinkSpamProtection(bot))
