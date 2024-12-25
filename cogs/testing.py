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

    @discord.app_commands.command(name="geartest")
    async def gear_test(self, interaction: discord.Interaction):
        view = ButtonGearView()
        await interaction.response.send_message("Choose gear slot to edit", view=view)
        await view.wait()
        if view.choice == -1:
            await interaction.delete_original_response()
        else:
            await interaction.edit_original_response(content=f"You selected: {view.choice}")
            await asyncio.sleep(6.0)
            await interaction.delete_original_response()


class ButtonGearView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice: int
        self.event = asyncio.Event()

    @discord.ui.button(label="Head", style=discord.ButtonStyle.blurple)
    async def head_button(self, interaction: discord.Interaction, button):
        self.choice = 0
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Chest", style=discord.ButtonStyle.blurple)
    async def chest_button(self, interaction: discord.Interaction, button):
        self.choice = 1
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Hands", style=discord.ButtonStyle.blurple)
    async def hands_button(self, interaction: discord.Interaction, button):
        self.choice = 2
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Legs", style=discord.ButtonStyle.blurple)
    async def legs_button(self, interaction: discord.Interaction, button):
        self.choice = 3
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="👢")
    async def feet_button(self, interaction: discord.Interaction, button):
        self.choice = 4
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red)
    async def back_button(self, interaction: discord.Interaction, button):
        self.choice = -1
        await interaction.response.defer()
        self.event.set()

    async def wait(self):
        await self.event.wait()

async def setup(bot):
    await bot.add_cog(Testing(bot))

   