import discord
from discord.ext import commands
from discord import app_commands
import json, os

CONFIG_FILE = "data/config.json"
os.makedirs("data", exist_ok=True)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_config(
        self,
        guild_id: int,
        admin_channel_id: int,
        complaint_channel_id: int,
        setup_owner_id: int
    ):
        data = load_config()

        data[str(guild_id)] = {
            "setup_owner_id": setup_owner_id,
            "admin_channel_id": admin_channel_id,
            "log_channel_id": admin_channel_id,  # 🔥 SAME AS ADMIN CHANNEL
            "complaint_channel_id": complaint_channel_id,
            "trusted_admins": [setup_owner_id],
            "auto_punish": True,
            "punishment_type": "ban"
        }

        save_config(data)

        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(admin_channel_id)
        member = guild.get_member(setup_owner_id)

        if channel and member:
            embed = discord.Embed(
                title="🛡️ Vikrant Setup Complete",
                description="Server security has been configured successfully.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Trusted Admin",
                value=member.mention,
                inline=False
            )
            embed.add_field(
                name="Log Channel",
                value=channel.mention,
                inline=False
            )
            embed.set_footer(text="Vikrant • Auto-Security Setup")

            await channel.send(embed=embed)

    @app_commands.command(name="setup", description="Initial setup for Vikrant Security Bot")
    async def setup(self, interaction: discord.Interaction):
        guild = interaction.guild

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You must be an administrator to run setup.",
                ephemeral=True
            )
            return

        data = load_config()
        guild_data = data.get(str(guild.id))

        if guild_data:
            owner_id = guild_data.get("setup_owner_id")
            if interaction.user.id not in (owner_id, guild.owner_id):
                await interaction.response.send_message(
                    "🚫 This server is already configured.\n"
                    "Only the **original setup owner** or **server owner** can reconfigure.",
                    ephemeral=True
                )
                return

        view = SetupChoiceView(self, interaction)
        await interaction.response.send_message(
            "**🔧 Vikrant Setup**\nChoose how you want to configure the server:",
            view=view,
            ephemeral=True
        )


class SetupChoiceView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction

    @discord.ui.button(label="Auto Create Channels", style=discord.ButtonStyle.success)
    async def auto_create(self, interaction: discord.Interaction, _):
        guild = interaction.guild

        overwrites_admin = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_admin[role] = discord.PermissionOverwrite(view_channel=True)

        admin_channel = await guild.create_text_channel(
            "vikrant-admin",
            overwrites=overwrites_admin
        )

        overwrites_complaint = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_complaint[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        complaint_channel = await guild.create_text_channel(
            "complaints",
            overwrites=overwrites_complaint
        )

        await self.cog.save_config(
            guild.id,
            admin_channel.id,
            complaint_channel.id,
            interaction.user.id
        )

        await interaction.response.edit_message(
            content=(
                "✅ **Setup Complete!**\n"
                f"- Admin / Log Channel: {admin_channel.mention}\n"
                f"- Complaint Channel: {complaint_channel.mention}"
            ),
            view=None
        )

    @discord.ui.button(label="Manual Setup", style=discord.ButtonStyle.secondary)
    async def manual_setup(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(
            content="🔧 Select channels below:",
            view=ManualChannelSelectionView(self.cog, interaction)
        )


class ManualChannelSelectionView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.admin_channel = None
        self.complaint_channel = None

        self.add_item(AdminChannelDropdown(self))
        self.add_item(ComplaintChannelDropdown(self))
        self.add_item(ConfirmButton(self))


class AdminChannelDropdown(discord.ui.Select):
    def __init__(self, view):
        self.view_ref = view
        options = [
            discord.SelectOption(label=c.name, value=str(c.id))
            for c in view.interaction.guild.text_channels
        ]
        super().__init__(placeholder="Select Admin / Log Channel", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.admin_channel = int(self.values[0])
        await interaction.response.send_message(
            f"✅ Admin & Log channel set to <#{self.values[0]}>",
            ephemeral=True
        )


class ComplaintChannelDropdown(discord.ui.Select):
    def __init__(self, view):
        self.view_ref = view
        options = [
            discord.SelectOption(label=c.name, value=str(c.id))
            for c in view.interaction.guild.text_channels
        ]
        super().__init__(placeholder="Select Complaint Channel", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.complaint_channel = int(self.values[0])
        await interaction.response.send_message(
            f"✅ Complaint channel set to <#{self.values[0]}>",
            ephemeral=True
        )


class ConfirmButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Confirm Setup", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if not self.view_ref.admin_channel or not self.view_ref.complaint_channel:
            await interaction.response.send_message(
                "⚠️ Select both channels first.",
                ephemeral=True
            )
            return

        await self.view_ref.cog.save_config(
            interaction.guild.id,
            self.view_ref.admin_channel,
            self.view_ref.complaint_channel,
            interaction.user.id
        )

        await interaction.response.edit_message(
            content="✅ **Manual setup completed successfully.**",
            view=None
        )


async def setup(bot):
    await bot.add_cog(Setup(bot))
