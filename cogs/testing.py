import discord
from discord.ext import commands
import asyncio

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):
        pass

    async def combat(self, interaction:discord.Interaction):
        pass


class Item():
    def __init__(self, value:int, quantity:int, stack_size:int):
        self.value = value
        self.stack_size = stack_size
        self.quantity = quantity


class Drops():
    def __init__(self, xp:int, gold:int, item:Item|None):
        self.xp = xp
        self.gold = gold
        self.item = item
        

class Enemy():
    def __init__(self, name:str, hp:int, resist:float, speed:int, dmg:int, cc:float, cm:int, drops:Drops):
        self.name = name
        self.hp = hp
        self.resist = resist
        self.speed = speed
        self.dmg = dmg
        self.cc = cc
        self.cm = cm
        self.drops = drops


class TestDummy(Enemy):
    def __init__(self):
        super().__init__("Training Dummy", 9999, 0, 0, 0, 0, 0, Drops(1, 1, None))


class Weapon(Item):
    def __init__(self, value, dmg, rng, cc, cm, acc, slots):
        super().__init__(value, quantity=1, stack_size=1)
        self.dmg:int = dmg
        self.rng:int = rng
        self.cc:float = cc
        self.cm:float = cm
        self.acc:float = acc
        self.slots:int = slots


async def setup(bot):
    await bot.add_cog(Testing(bot))