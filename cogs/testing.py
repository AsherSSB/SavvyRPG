import discord
from discord.ext import commands
import asyncio

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot




async def setup(bot):
    await bot.add_cog(Testing(bot))