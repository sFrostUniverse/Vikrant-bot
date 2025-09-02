import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.logger import setup_logger
from keep_alive import keep_alive

# Start the keep-alive server (Render/Replit/other hosting)
keep_alive()

# Setup logging
setup_logger()

# Load bot token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False  # Track slash sync status

    async def setup_hook(self):
        """Load cogs before the bot is ready."""
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        # Sync slash commands globally (only once per run)
        try:
            synced = await self.tree.sync()
            print(f"🌍 Globally synced {len(synced)} slash command(s).")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} ({self.user.id})")


# Initialize bot
client = MyBot()

# Run bot (handles aiohttp session cleanup automatically)
if __name__ == "__main__":
    client.run(TOKEN)
