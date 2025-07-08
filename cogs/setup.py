import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui
import json, os

CONFIG_FILE = "data/config.json"

class ConfirmView(ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.value = None

    @ui.button(label="I Agree", style=discord.ButtonStyle.danger)
    async def agree(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Only the server owner can confirm this!", ephemeral=True)
            return
        self.value = True
        await interaction.response.edit_message(content="✅ Setup confirmed! Proceeding with configuration...", view=None)
        self.stop()

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(CONFIG_FILE):
            os.makedirs("data", exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)

    def save_config(self, guild_id, owner_id):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        config[str(guild_id)] = {"owner_id": owner_id, "setup_done": True}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    @app_commands.command(name="setup", description="Configure Vikrant in your server")
    async def setup(self, interaction: Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the **server owner** can run this command!", ephemeral=True)

        # Check for admin permissions
        if not interaction.user.guild_permissions.administrator:
            view = ConfirmView(interaction.user)
            await interaction.response.send_message(
                "**🚨 Potential risks with current setup**\n"
                "Administrator permissions were not provided to **Vikrant**!\n"
                "Without admin permissions, Vikrant may not be able to fully protect the server.\n\n"
                "⚠️ If you understand the risks and would like to proceed, click **'I Agree'**.",
                view=view,
                ephemeral=True
            )
            await view.wait()
            if not view.value:
                return  # Do nothing if the user didn't click

        # Save config
        self.save_config(interaction.guild_id, interaction.user.id)
        await interaction.followup.send(f"✅ Setup complete, <@{interaction.user.id}>!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
