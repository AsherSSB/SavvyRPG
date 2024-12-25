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
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Choose gear slot to edit", view=view)
        await view.wait()
        if view.choice == -1:
            await interaction.delete_original_response()
        else:
            await interaction.edit_original_response(content=f"You selected: {view.choice}")
            await asyncio.sleep(6.0)
            await interaction.delete_original_response()



class GearSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(max_values=1)
        self.add_option(label="Head", value="0")
        self.add_option(label="Chest", value="1")
        self.add_option(label="Hands", value="2")
        self.add_option(label="Legs", value="3")
        self.add_option(label="Feet", value="4")

    async def callback(self, interaction):
        self.view.choice = int(self.values[0])
        await interaction.response.defer()
        self.view.event.set()


class ButtonGearView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__()
        self.interaction: discord.Interaction
        self.choice: int
        self.event = asyncio.Event()
        self.method = 0
        self.buttons = []

        button_dict = [
            {"label": "Head", "style": discord.ButtonStyle.blurple},
            {"label": "Chest", "style": discord.ButtonStyle.blurple},
            {"label": "Hands", "style": discord.ButtonStyle.blurple},
            {"label": "Legs", "style": discord.ButtonStyle.blurple},
            {"label": None, "style": discord.ButtonStyle.blurple, "emoji": "👢"}
        ]
        
        # Create and add buttons
        for i, btn in enumerate(button_dict):
            button = discord.ui.Button(
                label=btn["label"],
                style=btn["style"],
                emoji=btn.get("emoji"),
                row=0
            )
            button.callback = self.create_callback(i)
            self.buttons.append(button)
        
        for button in self.buttons:
            self.add_item(button)

    def create_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            self.choice = choice
            await interaction.response.defer()
            self.event.set()
        return callback
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.red, row=2)
    async def back_button(self, interaction: discord.Interaction, button):
        self.choice = -1
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Swap Select Method", style=discord.ButtonStyle.green, row=2)
    async def swap_method_button(self, interaction: discord.Interaction, button):
        self.choice = -2
        await interaction.response.defer()
    
    async def swap_to_buttons(self):
        for child in filter(lambda x: isinstance(x, discord.ui.Select)):
            self.remove_item(child)
        for button in self.buttons:
            self.add_item(button)
        await self.interaction.edit_original_response(view=self)


    async def wait(self):
        await self.event.wait()

async def setup(bot):
    await bot.add_cog(Testing(bot))

   