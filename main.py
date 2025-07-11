import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from utils.logger import setup_logger
from keep_alive import keep_alive

# Start the keep-alive server (Render/Replit)
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

# Initialize bot
client = commands.Bot(command_prefix="!", intents=intents)
client.synced = False

# Load all cogs from /cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

# Sync slash commands globally
@client.event
async def on_ready():
    await client.wait_until_ready()
    try:
        synced = await client.tree.sync()
        print(f"🌍 Globally synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(f"✅ Logged in as {client.user} ({client.user.id})")

# Entry point
async def main():
    await load_cogs()
    await client.start(TOKEN)

# Run the bot
asyncio.run(main())
