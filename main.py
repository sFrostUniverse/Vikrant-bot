import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from utils.logger import setup_logger
from keep_alive import keep_alive

keep_alive()


from keep_alive import keep_alive
keep_alive()


setup_logger()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)
client.synced = False 

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

GUILD_ID = 1390547002693255331  

@client.event
async def on_ready():
    await client.wait_until_ready()
    try:
        synced = await client.tree.sync()
        print(f"✅ Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")



async def main():
    await load_cogs()  
    await client.start(TOKEN)

asyncio.run(main())
