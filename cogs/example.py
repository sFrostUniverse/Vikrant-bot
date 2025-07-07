from discord.ext import commands

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong! Vikrant is online and alert.")

async def setup(bot):  # <-- make this async!
    await bot.add_cog(Example(bot))  # <-- await this too!
