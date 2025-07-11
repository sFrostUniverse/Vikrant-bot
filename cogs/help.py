import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

GITHUB_URL = "https://github.com/sFrostUniverse/Vikrant-bot"
IMAGE_URL = "attachment://INS_Vikrant.jpg"  # Refers to the attached file

class CommandsModal(ui.Modal, title="📜 Vikrant Command Deck"):
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
        await interaction.response.send_message("📬 Commands sent above, Commander.", ephemeral=True)

class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="🌐 GitHub", url=GITHUB_URL))

    @ui.button(label="🛠️ Launch Setup", style=discord.ButtonStyle.primary, custom_id="setup_btn")
    async def setup_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message("To initiate security setup, type `/setup`.", ephemeral=True)

    @ui.button(label="📜 View Commands", style=discord.ButtonStyle.secondary, custom_id="commands_btn")
    async def commands_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(CommandsModal())

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Access Vikrant's command and protection systems.")
    async def help(self, interaction: Interaction):
        embed = discord.Embed(
            title="🛡️ INS Vikrant – Server Defense Command",
            description=(
                "**Mission:** Safeguard your Discord server from nukes, raids, link spam, and rogue admins.\n\n"
                "🧭 Use `/setup` to deploy Vikrant's protective systems.\n"
                "🛠 Configure trusted admins, auto-punishments, and emergency responses."
            ),
            color=discord.Color.dark_blue()
        )
        embed.add_field(
            name="🎯 Core Systems Online",
            value=(
                "`Anti-Nuke` `Auto-Punish` `Trusted Admins`\n"
                "`Complaint Channel` `Lockdown Mode` `Link Spam Detection`"
            ),
            inline=False
        )
        embed.add_field(
            name="📌 Motto",
            value="*“Peace Through Preparedness. Protection Without Fail.”*",
            inline=False
        )
        embed.set_footer(text="Vikrant | Indian Navy Inspired Defense AI", icon_url="https://em-content.zobj.net/thumbs/120/apple/354/anchor_2693.png")
        embed.set_image(url=IMAGE_URL)

        file = discord.File("INS_Vikrant_(R11)_and_INS_Vikramaditya_(R33)_during_joint_exercise_(cropped).jpg", filename="INS_Vikrant.jpg")

        await interaction.response.send_message(embed=embed, view=HelpView(), ephemeral=True, files=[file])

async def setup(bot):
    await bot.add_cog(Help(bot))
