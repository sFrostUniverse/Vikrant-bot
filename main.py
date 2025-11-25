import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.logger import setup_logger

setup_logger()
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

        try:
            synced = await self.tree.sync()
            print(f"🌍 Synced {len(synced)} slash command(s)")
        except Exception as e:
            print(f"❌ Slash sync error: {e}")

    async def on_ready(self):
        print(f"🔋 Bot is online as {self.user} ({self.user.id})")

client = MyBot()

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except Exception as e:
        print("❌ Bot failed to start:", e)
