import discord
from discord.ext import commands


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Testing(bot))
