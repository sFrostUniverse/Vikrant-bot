import random
import asyncio
import discord
from discord import app_commands

def require_2fa():
    async def predicate(interaction: discord.Interaction):
        user = interaction.user
        code = str(random.randint(1000, 9999))

        try:
            
            await user.send(
                f"🔐 **2FA Confirmation Required**\n"
                f"You tried to run `{interaction.command.name}` in **{interaction.guild.name}**.\n"
                f"Please reply with the following code to confirm:\n\n**`{code}`**"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM. Please enable DMs from server members to use this command.",
                ephemeral=True
            )
            return False

        def check(msg):
            return msg.author.id == user.id and msg.content.strip() == code

        try:
            msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
            return True
        except asyncio.TimeoutError:
            await user.send("⏰ 2FA timed out. The command was cancelled.")
            return False

    return app_commands.check(predicate)
