import discord
from discord.ext import commands
import asyncio
from dataclasses import dataclass, field, fields
from custom.playable_character import PlayableCharacter
from cogs.mainmenus import CharacterEmbed, CharacterView
from cogs.database import Database
from cogs.combat import Weapon, Item
import random
from custom.gearview import ButtonGearView
from custom.inventory import InventoryEmbed, InventoryView
from custom.stattable import Nomad

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
    def __init__(self, name, rarity, value, critchance=None, multicast=None, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 5, .05)
        super().__init__(name, rarity, stats, value=value)
        self.critchance: float | None = critchance
        self.multicast: float | None = multicast


class ChestGear(Gear):
    def __init__(self, name, rarity, value, healing=None, attacks=None, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.2, 10, 0.1)
        super().__init__(name, rarity, stats, value=value)
        self.healing: float | None = healing
        self.attacks: int | None = attacks


class HandGear(Gear):
    def __init__(self, name, rarity, value, critmult=None, attacks=None, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.03)
        super().__init__(name, rarity, stats, value=value)
        self.critmult: float | None = critmult
        self.attacks: int | None = attacks


class LegGear(Gear):
    def __init__(self, name, rarity, value, healing=None, critmult=None, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 10, 0.05)
        super().__init__(name, rarity, stats, value=value)
        self.healing: float | None = healing
        self.critmult: float | None = critmult


class FootGear(Gear):
    def __init__(self, name, rarity, value, moves=None, critchance=None, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.1)
        super().__init__(name, rarity, stats, value=value)
        self.moves: int | None = moves
        self.critchance: float | None = critchance


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
        new_gear = gear_type(name=name, rarity=rarity, value=1)
        for _ in attribute_count:
            # get random valid attribute
            att_name = self.get_random_attribute(gear_type)
            current_val = self.get_field_by_name(new_gear, att_name)
            if current_val is None:
                current_val = 0
            add_val = self.randomize_attribute_value(att_name)
            # TODO: scale add_val with rarity, weight and level
            if isinstance(add_val, float):
                new_val = round((current_val + add_val), 2)
            else:
                new_val = current_val + add_val
            # asign value to item
            self.set_field_by_name_value(new_gear, att_name, new_val)
        
        return new_gear
    
    def randomize_attribute_value(self, attribute: str):
        attribute_values = {
            "moves" : random.randint(1, 2),
            "critchance" : round(random.uniform(0.03, 0.12), 2),
            "critmult" : round(random.uniform(0.05, 0.25), 2),
            "attacks" : random.randint(1, 2),
            "multicast" : round(random.uniform(0.02, 0.08), 2),
            "healing" : round(random.uniform(0.08, 0.32), 2),
        }
        return attribute_values[attribute]
    
    def level_scale_gear(self):
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
    
    def get_field_by_name(self, gear, field):
        return getattr(gear, field, None)
    
    def set_field_by_name_value(self, gear, field, value):
        setattr(gear, field, value)

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)
        self.usercharacter: PlayableCharacter

    @discord.app_commands.command(name="randomloot")
    async def generate_random_gear(self, interaction: discord.Interaction):
        generator = LootGenerator(0, Nomad())
        randgear = generator.generate_loot()
        content = []
        
        for field in fields(type(randgear)):
            # Skip private fields
            if field.name.startswith('_'):
                continue
                
            value = getattr(randgear, field.name)
            # Format floats to 2 decimal places
            if isinstance(value, float):
                value = f"{value:.2f}"
                
            content.append(f"{field.name}: {value}")
        
        formatted_content = "\n".join(content)
        await interaction.response.send_message(formatted_content)


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


    @discord.app_commands.command(name="invtest")
    async def inventory_menu_test(self, interaction: discord.Interaction):
        dummy_inventory = [
            Item("Health Potion", "❤️", value=50, stack_size=99, quantity=15),
            Item("Mana Potion", "💙", value=75, stack_size=99, quantity=10),
            Item("Phoenix Down", "🪶", value=500, stack_size=10, quantity=3),
            Item("Iron Sword", "⚔️", value=100, stack_size=1, quantity=1),
            Item("Wooden Shield", "🛡️", value=50, stack_size=1, quantity=1),
            Item("Magic Scroll", "📜", value=200, stack_size=5, quantity=2),
            Item("Gold Ring", "💍", value=1000, stack_size=1, quantity=1),
            Item("Dragon Scale", "🐉", value=2000, stack_size=10, quantity=5),
            Item("Ancient Coin", "🪙", value=100, stack_size=999, quantity=50),
            Item("Healing Herb", "🌿", value=25, stack_size=99, quantity=30),
            Item("Magic Crystal", "💎", value=150, stack_size=50, quantity=12),
            Item("Steel Arrows", "🏹", value=5, stack_size=999, quantity=200)
        ]
        embed = InventoryEmbed(dummy_inventory)
        view = InventoryView(interaction, dummy_inventory, embed)
        await interaction.response.send_message(content="inventory", view=view, embed=embed)
        await view.wait()
        await interaction.edit_original_response(
            content=f"You chose {dummy_inventory[view.choice].name}",
            view=None, embed=None)


async def setup(bot):
    await bot.add_cog(Testing(bot))

   