import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

GITHUB_URL = "https://github.com/sFrostUniverse/Vikrant-bot"

# Modal that displays command list
class CommandsModal(ui.Modal, title="📜 Vikrant Commands"):
    commands_text = ui.TextInput(
        label="Command Reference",
        style=discord.TextStyle.paragraph,
        default=(
            "/setup - Begin interactive setup\n"
            "/config - Show protection config\n"
            "/trust @user - Add trusted admin\n"
            "/untrust @user - Remove trusted admin\n"
            "/panic - Emergency lockdown\n"
            "/lockdown - Lock all channels\n"
            "/unlock - Unlock channels\n"
            "/complain - Submit a complaint\n"
            "/help - Show this panel"
        ),
        required=False,
        max_length=400,
    )

    async def on_submit(self, interaction: Interaction):
        await interaction.response.send_message("📬 Commands sent above!", ephemeral=True)

# Buttons view for /help
class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="🌐 GitHub", url=GITHUB_URL))

    @ui.button(label="🛠️ Setup", style=discord.ButtonStyle.primary, custom_id="setup_btn")
    async def setup_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message("To start setup, type `/setup` in any channel.", ephemeral=True)

    @ui.button(label="📜 Commands", style=discord.ButtonStyle.secondary, custom_id="commands_btn")
    async def commands_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(CommandsModal())

# Help command
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View help, features, and command list for Vikrant.")
    async def help(self, interaction: Interaction):
        embed = discord.Embed(
            title="🛡️ Vikrant – Server Defender Bot",
            description=(
                "Protect your server from nukes, raids, and abuse with smart automation.\n"
                "Built by **sFrostUniverse**.\n\n"
                "Use `/setup` to get started."
            ),
            color=discord.Color.purple()
        )
        embed.add_field(
            name="⚙️ Features",
            value="`Anti-Nuke` `Auto-Punish` `Trusted Admins`\n"
                  "`Complaint System` `Lockdown Mode` `24/7 Protection`",
            inline=False
        )
        embed.set_footer(text="Vikrant is watching your server 👁")

        await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
