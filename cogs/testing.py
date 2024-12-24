import discord
from discord.ext import commands

class Testing(commands.Cog):
    def __init__(self):
        pass


async def setup(bot):
    await bot.add_cog(Testing(bot))

   