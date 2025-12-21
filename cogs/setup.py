import discord
from discord.ext import commands
from discord import app_commands
import json, os

CONFIG_FILE = "data/config.json"

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_config(self, guild_id, admin_channel_id, complaint_channel_id, trusted_admin_id):
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        data[str(guild_id)] = {
        "setup_owner_id": trusted_admin_id,   # 👈 OWNER WHO RAN SETUP
        "admin_log_channel": admin_channel_id,
        "complaint_channel_id": complaint_channel_id,
        "trusted_admins": [trusted_admin_id],
        "auto_punish": True,
        "punishment_type": "ban"
    }


        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(admin_channel_id)
        member = guild.get_member(trusted_admin_id)

        if channel and member:
            embed = discord.Embed(
                title="🛡️ Trusted Admin Assigned",
                description=f"{member.mention} has been assigned as a **Trusted Admin** during setup.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Role Summary",
                value="Trusted Admins can bypass anti-nuke punishments and help manage server security.",
                inline=False
            )
            embed.set_footer(text="Vikrant • Auto-Security Setup")
            await channel.send(embed=embed)

    @app_commands.command(name="setup", description="Initial server setup for Vikrant Security Bot")
    async def setup(self, interaction: discord.Interaction):
        guild = interaction.guild

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You must be an administrator to run setup.",
                ephemeral=True
            )
            return

        # 🔐 Load config if exists
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)

            guild_data = data.get(str(guild.id))

            if guild_data:
                stored_owner = guild_data.get("setup_owner_id")

                # ❌ Not original setup owner AND not Discord owner
                if interaction.user.id != stored_owner and interaction.user.id != guild.owner_id:
                    await interaction.response.send_message(
                        "🚫 This server is already configured.\n"
                        "Only the **original setup owner** or **server owner** can reconfigure Vikrant.",
                        ephemeral=True
                    )
                    return

        view = SetupChoiceView(self, interaction)
        await interaction.response.send_message(
            "**🔧 Setup Vikrant:**\nWould you like me to auto-create admin and complaint channels or configure manually?",
            view=view,
            ephemeral=True
        )


class SetupChoiceView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction

    @discord.ui.button(label="Auto Create", style=discord.ButtonStyle.success)
    async def auto_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        overwrites_admin = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_admin[role] = discord.PermissionOverwrite(view_channel=True)

        admin_channel = await guild.create_text_channel("vikrant-admin", overwrites=overwrites_admin)

        overwrites_complaint = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_complaint[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        complaint_channel = await guild.create_text_channel("complaints", overwrites=overwrites_complaint)

        await self.cog.save_config(guild.id, admin_channel.id, complaint_channel.id, interaction.user.id)

        await interaction.response.edit_message(
            content=f"✅ Setup complete!\n- Admin Channel: {admin_channel.mention}\n- Complaint Channel: {complaint_channel.mention}",
            view=None
        )

    @discord.ui.button(label="Manual Setup", style=discord.ButtonStyle.secondary)
    async def manual_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🔧 Please select the existing channels below.",
            view=ManualChannelSelectionView(self.cog, interaction),
        )

class ManualChannelSelectionView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction
        self.selected_admin_channel = None
        self.selected_complaint_channel = None

        self.add_item(AdminChannelDropdown(self))
        self.add_item(ComplaintChannelDropdown(self))
        self.add_item(ConfirmButton(self))

class AdminChannelDropdown(discord.ui.Select):
    def __init__(self, view):
        self.parent_view = view
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in view.interaction.guild.text_channels
        ]
        super().__init__(placeholder="Select Admin Channel", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_admin_channel = int(self.values[0])
        await interaction.response.send_message(f"✅ Admin channel set to <#{self.values[0]}>", ephemeral=True)

class ComplaintChannelDropdown(discord.ui.Select):
    def __init__(self, view):
        self.parent_view = view
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in view.interaction.guild.text_channels
        ]
        super().__init__(placeholder="Select Complaint Channel", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_complaint_channel = int(self.values[0])
        await interaction.response.send_message(f"✅ Complaint channel set to <#{self.values[0]}>", ephemeral=True)

class ConfirmButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label="Confirm Setup", style=discord.ButtonStyle.success)
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        if not self.parent_view.selected_admin_channel or not self.parent_view.selected_complaint_channel:
            await interaction.response.send_message("⚠️ Please select both channels before confirming.", ephemeral=True)
            return

        await self.parent_view.cog.save_config(
            interaction.guild.id,
            self.parent_view.selected_admin_channel,
            self.parent_view.selected_complaint_channel,
            interaction.user.id
        )

        await interaction.response.edit_message(
            content=f"✅ Manual setup complete!\n- Admin Channel: <#{self.parent_view.selected_admin_channel}>\n- Complaint Channel: <#{self.parent_view.selected_complaint_channel}>",
            view=None
        )

async def setup(bot):
    await bot.add_cog(Setup(bot))
