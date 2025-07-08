import discord
from discord.ext import commands
from discord import app_commands, Interaction
import json, os

CONFIG_FILE = "data/config.json"

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)

    def save_config(self, config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    @app_commands.command(name="setup", description="Configure Vikrant in your server")
    async def setup(self, interaction: Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the server owner can use this command!", ephemeral=True)

        with open(CONFIG_FILE) as f:
            config = json.load(f)

        config[str(interaction.guild_id)] = {
            "owner_id": interaction.user.id,
            "setup_done": True
        }

        self.save_config(config)

        await interaction.response.send_message(f"✅ Setup complete, <@{interaction.user.id}>!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
