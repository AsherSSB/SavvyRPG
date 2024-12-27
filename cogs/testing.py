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

EMBED_NEWLINE = "\u200b"

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


class InventoryEmbed(discord.Embed):
    def __init__(self, inventory: list[Item], title = "Inventory"):
        super().__init__(title=title)
        self.inventory = inventory
        self.page = 1
        self.initialize_with_blank_fields()
        self.update_items()

    # needed for set_field_at method in update_items to properly function
    def initialize_with_blank_fields(self):
    # Initialize pattern of 2 inline + 1 separator, repeated 5 times
        for i in range(5):  # 5 rows of 2 items each = 10 items total
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=True)
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=True)
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=False)

    # embed update from hell
    def update_items(self):
        slice_start = (self.page - 1) * 10
        max_items = min(len(self.inventory), slice_start + 10)
        working_inv = self.inventory[slice_start:max_items]
        
        field_index = 0  # Track actual field position including separators
        for i in range(0, len(working_inv), 2):
            # First item
            item = working_inv[i]
            self.set_field_at(field_index,
                name=f"{item.emoji} {item.name}",
                value=f"placeholder short description.\nQuantity:{item.quantity}\nWorth: {item.value}g each",
                inline=True)
            field_index += 1
            
            # Second item if exists
            if i + 1 < len(working_inv):
                item = working_inv[i + 1]
                self.set_field_at(field_index,
                    name=f"{item.emoji} {item.name}",
                    value=f"placeholder short description.\nQuantity:{item.quantity}\nWorth: {item.value}g each",
                    inline=True)
                field_index += 1
            else:
                # Empty second slot
                self.set_field_at(field_index,
                    name=EMBED_NEWLINE,
                    value=EMBED_NEWLINE,
                    inline=True)
                field_index += 1
                
            # Separator after pair
            self.set_field_at(field_index,
                name=EMBED_NEWLINE,
                value="\n\n\n",
                inline=False)
            field_index += 1

        # Clear remaining fields
        while field_index < 15:  # 15 total fields (5 rows × 3 fields per row)
            self.set_field_at(field_index,
                name=EMBED_NEWLINE,
                value=EMBED_NEWLINE,
                inline=True if field_index % 3 != 2 else False)
            field_index += 1
                

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
        self.view.embed.page -= 1
        await self.view.correct_inventory_response()


class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Next", emoji="➡️", row=1)

    async def callback(self, interaction):
        await interaction.response.defer()
        self.view.select.page += 1
        self.view.embed.page += 1
        await self.view.correct_inventory_response()


class InventoryView(discord.ui.View):
    def __init__(self, interaction, inventory: list[Item], embed):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.select = InventorySelect(inventory)
        self.embed: InventoryEmbed = embed
        self.event = asyncio.Event()
        self.back_button = PreviousButton()
        self.next_button = NextButton()
        self.add_item(self.back_button)
        self.add_item(self.next_button)
        self.add_item(self.select)
        self.choice = None

    async def correct_inventory_response(self):
        self.correct_buttons()
        self.correct_select()
        self.correct_embed()
        await self.interaction.edit_original_response(view=self, embed=self.embed)
    
    def correct_buttons(self):
        self.back_button.disabled = self.select.page <= 1

        total_pages = (len(self.select.inventory) + 9) // 10
        self.next_button.disabled = self.select.page >= total_pages

    def correct_select(self):
        self.select.update_options()

    def correct_embed(self):
        self.embed.update_items()

    async def wait(self):
        await self.event.wait()



async def setup(bot):
    await bot.add_cog(Testing(bot))

   