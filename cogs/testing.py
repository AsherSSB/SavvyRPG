import discord
from discord.ext import commands
import asyncio
from dataclasses import dataclass, field

@dataclass
class Item():
    name: str
    value: int = field(default=0, kw_only=True)
    stack_size: int = field(default=1, kw_only=True)
    quantity: int = field(default=1, kw_only=True)


@dataclass
class GearStatTable():
    resist: float
    maxhp: int
    dodge: float
    strength: int
    will: int
    dexterity: int
    intelligence: int
    attunement: int


@dataclass
class HeadGear():
    basestats: GearStatTable
    critchance: float
    multicast: float


@dataclass
class ChestGear():
    basestats: GearStatTable
    healing: float
    attacks: int


@dataclass
class HandGear():
    basestats: GearStatTable
    critmult: float
    attacks: int


@dataclass
class LegGear():
    basestats: GearStatTable
    healing: float


@dataclass
class FootGear():
    basestats: GearStatTable
    moves: int
    critchance: float


class Gear(Item):
    def __init__(self, name: str , value: int, slot: str):
        super().__init__(name=name, value=value, stack_size=1, quantity=1)
        self.slot: str = slot

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


class GearView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice: int
        self.event = asyncio.Event()


async def setup(bot):
    await bot.add_cog(Testing(bot))

   