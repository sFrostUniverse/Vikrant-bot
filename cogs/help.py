import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

GITHUB_URL = "https://github.com/sFrostUniverse/Vikrant-bot"


# ─────────────────────────────
# HELP VIEW
# ─────────────────────────────
class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)

        self.add_item(
            ui.Button(
                label="🌐 GitHub",
                url=GITHUB_URL,
                style=discord.ButtonStyle.link
            )
        )

    @ui.button(
        label="🛠 Run Setup",
        style=discord.ButtonStyle.primary
    )
    async def setup_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "🛠 To configure Vikrant, use:\n\n`/setup`",
            ephemeral=True
        )

    @ui.button(
        label="🛡 Trusted Admins",
        style=discord.ButtonStyle.secondary
    )
    async def trusted_admins_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "🛡 Manage trusted admins using:\n"
            "`/trusted_admins`\n"
            "`/trust @user`\n"
            "`/untrust @user`",
            ephemeral=True
        )

    @ui.button(
        label="📊 Logging",
        style=discord.ButtonStyle.secondary
    )
    async def logging_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "📊 Logs are automatic after setup.\n\n"
            "They record:\n"
            "• Member join / leave\n"
            "• Message edits & deletes\n"
            "• Voice moves (with moderator attribution)\n"
            "• Channel & role changes\n\n"
            "No further setup required.",
            ephemeral=True
        )


# ─────────────────────────────
# HELP COG
# ─────────────────────────────
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show Vikrant Security command panel"
    )
    async def help(self, interaction: Interaction):
        embed = discord.Embed(
            title="🛡 Vikrant Security System",
            description=(
                "**Mission:** Protect your server from raids, nukes, and abuse.\n\n"
                "Vikrant is a **defensive moderation bot** inspired by real-world security systems.\n"
                "Once configured, protection runs **automatically**."
            ),
            color=discord.Color.dark_blue()
        )

        embed.add_field(
            name="🚀 Getting Started",
            value="Run `/setup` once to initialize security.",
            inline=False
        )

        embed.add_field(
            name="🧠 Core Systems",
            value=(
                "• Anti-Nuke protection\n"
                "• Trusted Admin system\n"
                "• Persistent logging (Dyno-style)\n"
                "• Emergency lockdowns\n"
                "• Complaint handling"
            ),
            inline=False
        )

        embed.add_field(
            name="⚠️ Emergency Commands",
            value=(
                "`/panic` – Immediate lockdown\n"
                "`/lockdown` – Lock channels\n"
                "`/unlock` – Restore access"
            ),
            inline=False
        )

        embed.set_footer(
            text="Vikrant • Protection without compromise"
        )

        await interaction.response.send_message(
            embed=embed,
            view=HelpView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Help(bot))
