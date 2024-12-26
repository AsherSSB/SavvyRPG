import discord
from discord.ext import commands
import asyncio
from dataclasses import dataclass, field, fields
from custom.playable_character import PlayableCharacter
from cogs.mainmenus import CharacterEmbed, CharacterView
from cogs.database import Database
from cogs.combat import Weapon, Item
import random


@dataclass
class BonusStatsTable():
    strength: int | None = field(default=None, kw_only=True)
    will: int | None = field(default=None, kw_only=True)
    dexterity: int | None = field(default=None, kw_only=True)
    intelligence: int | None = field(default=None, kw_only=True)
    attunement: int | None = field(default=None, kw_only=True)


@dataclass
class GearStatTable():
    resist: float 
    maxhp: int
    dodge: float | None
    bonus_stats: BonusStatsTable


class Gear(Item):
    def __init__(self, name, rarity, stats, value=0):
        super().__init__(name, value=value)
        self.rarity: str = rarity
        self.stats: GearStatTable = stats
    
    # why the fuck did i put this here and not in the loot generator
    def randomize_gear_stats(self, maxres, maxhp, maxdodge):
        resist = round(random.uniform(maxres/5, maxres), 1)
        hp = random.randint(maxhp//5, maxhp)
        dodge: float = round(random.uniform(maxdodge/5, maxdodge), 1)
        return GearStatTable(resist, hp, dodge)


class HeadGear(Gear):
    def __init__(self, name, rarity, value, critchance, multicast, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 5, .05)
        super().__init__(name, rarity, stats, value=value)
        self.critchance: float = critchance
        self.multicast: float = multicast


class ChestGear(Gear):
    def __init__(self, name, rarity, value, healing, attacks, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.2, 10, 0.1)
        super().__init__(name, rarity, stats, value=value)
        self.healing: float = healing
        self.attacks: int = attacks


class HandGear(Gear):
    def __init__(self, name, rarity, value, critmult, attacks, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.03)
        super().__init__(name, rarity, stats, value=value)
        self.critmult: float = critmult
        self.attacks: int = attacks


class LegGear(Gear):
    def __init__(self, name, rarity, value, healing, critmult, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 10, 0.05)
        super().__init__(name, rarity, stats, value=value)
        self.healing: float = healing
        self.critmult: float = critmult


class FootGear(Gear):
    def __init__(self, name, rarity, value, moves, critchance, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.1)
        super().__init__(name, rarity, stats, value=value)
        self.moves: int = moves
        self.critchance: float = critchance


class LootGenerator():
    def __init__(self, player_level, player_origin):
        self.rarity_list = ["Common", "Uncommon", "Rare", "Exotic", "Mythical"]
        self.rarity_chances = [0.7, 0.2, 0.06, 0.03, .01]
        self.weights = ["Light", "Medium", "Heavy"]
        self.gear_list = [HeadGear, ChestGear, HandGear, LegGear, FootGear]
        self.level = player_level
        self.origin = player_origin

    def generate_loot(self):
        type_names = {
            HeadGear : "Helmet",
            ChestGear : "Chestplate",
            HandGear : "Gloves", 
            LegGear : "Pants", 
            FootGear : "Shoes"
        }
        special_att_counts = {
            "Common" : 0,
            "Uncommon" : 1,
            "Rare" : 2, 
            "Exotic" : 3,
            "Mythical" : 4
        }
        # TODO: move to seperate function
        base_stat_rarity_scaling = {
            "Common" : 1.0,
            "Uncommon" : 1.5,
            "Rare" : 2, 
            "Exotic" : 2.5,
            "Mythical" : 3.0
        }
        rarity = self.choose_rarity()
        gear_type = self.choose_random_gear_type()
        name = type_names[gear_type]
        attribute_count = special_att_counts[rarity]
        for _ in attribute_count:
            # add attribute to gear
            pass
        

    def level_scale_gear():
        pass

    def choose_rarity(self):
        return random.choices(
            population=self.rarity_list, 
            weights=self.rarity_chances, k=1)[0]

    def choose_random_gear_type(self):
        return random.choice(self.gear_list)
    
    def get_random_attribute(self, gear_class):
        # Get all fields except common ones from base classes
        gear_fields = [field.name for field in fields(gear_class) 
                      if field.name not in ['name', 'rarity', 'value', 'stats', 'stack_size', 'quantity']]
        return random.choice(gear_fields)

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)
        self.usercharacter: PlayableCharacter

    @discord.app_commands.command(name="charactermenutesting")
    async def send_character_menu(self, interaction:discord.Interaction):
        self.usercharacter = self.db.get_character(interaction.user.id)
        embed = CharacterEmbed(self.usercharacter)
        view = CharacterView()
        await interaction.response.send_message(content="Character", embed=embed, view=view)
        await view.wait()
        if view.choice == 0:
            await self.send_gear_type_selection_menu(view.interaction)
        else:
            await view.interaction.response.defer()
        
    @discord.app_commands.command(name="gear")
    async def gear_test(self, interaction: discord.Interaction):
        await self.send_gear_type_selection_menu(interaction)

    async def send_gear_type_selection_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Choose gear slot to edit", view=view)
        await view.wait()
        if view.choice == -1:
            await interaction.delete_original_response()
        else:
            await interaction.edit_original_response(content=f"You selected: {view.labels[view.choice]}")
            await asyncio.sleep(6.0)
            await interaction.delete_original_response()


# TODO: implement these
class InventoryEmbed(discord.Embed):
    def __init__(self, inventory: list[Item], title = "Inventory"):
        super().__init__(title=title)
        self.inventory = inventory


class InventorySelect(discord.ui.Select):
    def __init__(self, inventory: list[Item], placeholder="Select Item", max_values=1, row=0):
        super().__init__(placeholder=placeholder, min_values=1, max_values=max_values, row=row)
        self.inventory = inventory
        self.page = 1
        self.update_options()

    def update_options(self):
        max_items = min(len(self.inventory), self.page * 10)
        slice_start = (self.page - 1) * 10
        # Create new options list
        self.options = [
            discord.SelectOption(
                label=item.name, 
                emoji=item.emoji,
                value=f"{i}"
            ) for i, item in enumerate(self.inventory[slice_start:max_items], slice_start)
        ]

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = int(self.values[0])
        await interaction.response.defer()
        self.view.event.set()


class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Previous", emoji="⬅️", row=1, disabled=True)

    async def callback(self, interaction):
        await interaction.response.defer()
        self.view.select.page -= 1
        self.view.correct_buttons()


class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Next", emoji="➡️", row=1)

    async def callback(self, interaction):
        await interaction.response.defer()
        self.view.select.page += 1
        self.view.correct_buttons()


class InventoryView(discord.ui.View):
    def __init__(self, interaction, inventory: list[Item]):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.select = InventorySelect(inventory)
        self.embed = InventoryEmbed()
        self.event = asyncio.Event()
        self.back_button = PreviousButton()
        self.next_button = NextButton()
        self.add_item(self.back_button)
        self.add_item(self.next_button)

    
    async def correct_buttons(self):
        self.back_button.disabled = self.select.page <= 1

        total_pages = (len(self.select.inventory) + 9) // 10
        self.next_button.disabled = self.select.page >= total_pages

    async def wait(self):
        await self.event.wait()

class GearSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(max_values=1)
        self.add_option(label="Head", value="0", emoji="🧢")
        self.add_option(label="Chest", value="1", emoji="👕")
        self.add_option(label="Hands", value="2", emoji="🧤")
        self.add_option(label="Legs", value="3", emoji="👖")
        self.add_option(label="Feet", value="4", emoji="👢")

    async def callback(self, interaction):
        self.view.choice = int(self.values[0])
        await interaction.response.defer()
        self.view.event.set()


class ButtonGearView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.choice: int
        self.event = asyncio.Event()
        self.method = 0
        self.style = 0
        self.labels = ["Head","Chest","Hands","Legs","Feet"]
        self.buttons = []
        self.select: discord.SelectMenu = GearSelect()

        button_dict = [
            {"label": "Head", "style": discord.ButtonStyle.gray, "emoji": "🧢"}, 
            {"label": "Chest", "style": discord.ButtonStyle.gray, "emoji": "👕"},
            {"label": "Hands", "style": discord.ButtonStyle.gray, "emoji": "🧤"},
            {"label": "Legs", "style": discord.ButtonStyle.gray, "emoji": "👖"}, 
            {"label": "Feet", "style": discord.ButtonStyle.gray, "emoji": "👢"}
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
        if self.method == 0:
            self.method = 1
            await self.swap_to_select()
        else:
            self.method = 0
            await self.swap_to_buttons()
        await interaction.response.defer()

    @discord.ui.button(label="Swap Styles", style=discord.ButtonStyle.green, row=2)
    async def swap_style_button(self, interaction: discord.Interaction, button):
        if self.style == 0:
            self.style = 1
            await self.remove_button_text()
            await self.remove_select_text()
        else:
            self.style = 0
            await self.add_button_text()
            await self.add_select_text()
        await interaction.response.defer()
        await self.interaction.edit_original_response(view=self)

    async def add_select_text(self):
        for i, option in enumerate(self.select.options):
            option.label = self.labels[i]

    async def add_button_text(self):
        for i, button in enumerate(self.buttons):
            button.label = self.labels[i]
    
    async def remove_button_text(self):
        for button in self.buttons:
            button.label = ""

    async def remove_select_text(self):
        for option in self.select.options:
            option.label = "⠀"

    async def swap_to_buttons(self):
        self.remove_item(self.select)
        for button in self.buttons:
            self.add_item(button)
        await self.interaction.edit_original_response(view=self)

    async def swap_to_select(self):
        for button in self.buttons:
            self.remove_item(button)
        self.add_item(self.select)
        await self.interaction.edit_original_response(view=self)

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Testing(bot))

   