import discord
from discord.ext import commands
from discord import app_commands
import json, os

CONFIG_FILE = "data/config.json"

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_config(self, guild_id, admin_channel_id, complaint_channel_id):
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        data[str(guild_id)] = {
            "admin_channel_id": admin_channel_id,
            "complaint_channel_id": complaint_channel_id
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @app_commands.command(name="setup", description="Initial server setup for Vikrant Security Bot")
    async def setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You must be an administrator to run setup.", ephemeral=True)
            return

        # Check existing channels
        admin_channel = discord.utils.get(interaction.guild.text_channels, name="vikrant-admin")
        complaint_channel = discord.utils.get(interaction.guild.text_channels, name="complaints")

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

        # Create admin channel (private to admins)
        overwrites_admin = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_admin[role] = discord.PermissionOverwrite(view_channel=True)

        admin_channel = await guild.create_text_channel("vikrant-admin", overwrites=overwrites_admin)

        # Create complaint channel (visible to all, but only admins can read/write)
        overwrites_complaint = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites_complaint[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        complaint_channel = await guild.create_text_channel("complaints", overwrites=overwrites_complaint)

        await self.cog.save_config(guild.id, admin_channel.id, complaint_channel.id)

        await interaction.response.edit_message(
            content=f"✅ Setup complete!\n- Admin Channel: {admin_channel.mention}\n- Complaint Channel: {complaint_channel.mention}",
            view=None
        )

    @discord.ui.button(label="Manual Setup", style=discord.ButtonStyle.secondary)
    async def manual_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔧 Please mention the admin and complaint channels or provide their IDs.",
            ephemeral=True
        )

# In your main file
async def setup(bot):
    await bot.add_cog(Setup(bot))
