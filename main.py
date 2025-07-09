import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from utils.logger import setup_logger
from keep_alive import keep_alive

# Start the keep-alive web server (for Render or Replit hosting)
keep_alive()

# Setup logging
setup_logger()

# Load bot token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configure Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Needed for reading message content
intents.guilds = True
intents.members = True  # Good for tracking trusted admins, moderation, etc.

# Initialize the bot
client = commands.Bot(command_prefix="!", intents=intents)
client.synced = False

# Load all cogs from /cogs folder
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

# Sync slash commands globally (takes time to show across all servers)
@client.event
async def on_ready():
    await client.wait_until_ready()
    try:
        synced = await client.tree.sync()  # GLOBAL sync for all servers
        print(f"🌍 Globally synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(f"✅ Logged in as {client.user} ({client.user.id})")

# Main async entry point
async def main():
    await load_cogs()
    await client.start(TOKEN)

# Run the bot
asyncio.run(main())
