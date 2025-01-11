import discord
from discord.ext import commands
from cogs.database import Database
from custom.gear import HandGear, HeadGear, GearStatTable, Item, BonusStatsTable
from custom.gear import Loadout


class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Testing(bot))
