import discord
from discord.ext import commands
import asyncio
from custom.weapons import Sword

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def test(self):
        swrd = Sword().__dict__
        inventory = [
            {"item_id": 1, "name": "Sword", "quantity": 1},
            {"item_id": 2, "name": "Shield", "quantity": 1},
            {"item_id": 3, "name": "Health Potion", "quantity": 5}
        ]
        print(len(inventory))


async def setup(bot):
    await bot.add_cog(Testing(bot))