import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.logger import setup_logger
from keep_alive import keep_alive

load_dotenv()
setup_logger()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[FrostNews] Logged in as {bot.user} (ID: {bot.user.id})")

    extensions = ["cogs.news", "cogs.setup", "cogs.reconfigure", "cogs.help"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"[FrostNews] Loaded extension: {ext}")
        except Exception as e:
            print(f"[FrostNews] Failed to load {ext}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"[FrostNews] Synced {len(synced)} slash commands globally.")
    except Exception as e:
        print(f"[FrostNews] Command sync failed: {e}")

keep_alive()
bot.run(TOKEN)
