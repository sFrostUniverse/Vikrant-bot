import discord
from discord.ext import commands

class Lockdown(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.locked_channels = {}


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        self.locked_channels[ctx.guild.id] = []
        for channel in ctx.guild.text_channels:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            if overwrite.send_messages is False:
                continue  
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            self.locked_channels[ctx.guild.id].append(channel.id)
        await ctx.send("🔒 All channels are now in lockdown.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
        locked = self.locked_channels.get(ctx.guild.id, [])
        if not locked:
            return await ctx.send("⚠️ No channels were previously locked.")
        
        for channel in ctx.guild.text_channels:
            if channel.id in locked:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = None  # reset permission
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        self.locked_channels[ctx.guild.id] = []
        await ctx.send("🔓 Lockdown lifted, channels are now open.")

async def setup(bot):
    await bot.add_cog(Lockdown(bot))




