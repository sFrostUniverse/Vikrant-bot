import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.locked_channels = {}

    @app_commands.command(name="lockdown", description="Lock all text channels in the server")
    @app_commands.checks.has_permissions(administrator=True)
    async def lockdown(self, interaction: Interaction):
        guild = interaction.guild
        self.locked_channels[guild.id] = []

        for channel in guild.text_channels:
            overwrite = channel.overwrites_for(guild.default_role)
            if overwrite.send_messages is False:
                continue
            overwrite.send_messages = False
            await channel.set_permissions(guild.default_role, overwrite=overwrite)
            self.locked_channels[guild.id].append(channel.id)

        await interaction.response.send_message("🔒 All text channels are now in lockdown.")

    @app_commands.command(name="unlock", description="Unlock all previously locked text channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock(self, interaction: Interaction):
        guild = interaction.guild
        locked = self.locked_channels.get(guild.id, [])

        if not locked:
            return await interaction.response.send_message("⚠️ No channels were previously locked.")

        for channel in guild.text_channels:
            if channel.id in locked:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(guild.default_role, overwrite=overwrite)

        self.locked_channels[guild.id] = []
        await interaction.response.send_message("🔓 Lockdown lifted, all channels are now open.")

async def setup(bot):
    await bot.add_cog(Lockdown(bot))
