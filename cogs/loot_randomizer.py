import discord
from discord.ext import commands
import asyncio
from dataclasses import fields
from custom.playable_character import PlayableCharacter
from cogs.database import Database
from custom.gear import Item
import random
from custom.gearview import ButtonGearView
from custom.inventory import InventoryEmbed, InventoryView
from custom.stattable import Nomad
from custom.gear import Gear, HeadGear, ChestGear, HandGear, LegGear, FootGear, GearStatTable, BonusStatsTable


class LootGenerator():
    def __init__(self, player_level, player_origin):
        self.rarity_list = ["Common", "Uncommon", "Rare", "Exotic", "Mythical"]
        self.rarity_chances = [0.7, 0.2, 0.06, 0.03, .01]
        self.weights = ["Light", "Medium", "Heavy"]
        self.gear_list = [HeadGear, ChestGear, HandGear, LegGear, FootGear]
        self.level = player_level
        self.origin = player_origin
        self.rarity_scaling = {
            "Common": 1.0,
            "Uncommon": 1.5,
            "Rare": 2,
            "Exotic": 2.5,
            "Mythical": 3.0
        }

    def generate_loot(self):
        type_names = {
            HeadGear: "Helmet",
            ChestGear: "Chestplate",
            HandGear: "Gloves",
            LegGear: "Pants",
            FootGear: "Shoes"
        }
        # TODO: move attribute assigning to different function
        special_att_counts = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Exotic": 3,
            "Mythical": 4
        }

        rarity = self.choose_rarity()
        gear_type = self.choose_random_gear_type()
        weight = self.choose_random_weight()
        name = weight + type_names[gear_type]

        attribute_count = special_att_counts[rarity]
        stats = self.generate_random_stats(gear_type)
        new_gear: Gear = gear_type(name=name, rarity=rarity, stats=stats, value=1)
        self.scale_base_stats_with_rarity(new_gear)
        self.scale_base_stats_with_weight(weight, new_gear.stats)
        self.scale_base_stats_with_level(new_gear.stats, self.level)
        # add special stats/attributes
        for _ in range(attribute_count):
            # get random valid attribute
            att_name = self.get_random_attribute(gear_type)
            current_val = self.get_field_by_name(new_gear, att_name)
            if current_val is None:
                current_val = 0
            add_val = self.randomize_attribute_value(att_name)
            add_val = self.scale_attribue_with_rarity(add_val, att_name, rarity)
            if isinstance(add_val, float):
                new_val = round((current_val + add_val), 2)
            else:
                new_val = current_val + add_val
            # asign value to item
            self.set_field_by_name_value(new_gear, att_name, new_val)

        return new_gear

    def scale_base_stats_with_level(self, stats: GearStatTable, level: int):
        stats.maxhp = int(stats.maxhp * (1 + 0.2 * level))

    def scale_base_stats_with_weight(self, weight, stats: GearStatTable):
        if weight == "Medium":
            return
        elif weight == "Light":
            self.scale_stats_light(stats)
        else:
            self.scale_stats_heavy(stats)

    def scale_stats_heavy(self, stats: GearStatTable):
        stats.dodge = 0.0
        stats.resist = round(stats.resist * 2, 2)
        stats.maxhp = int(stats.maxhp * 1.5)

    def scale_stats_light(self, stats: GearStatTable):
        stats.dodge = round(stats.dodge * 2, 2)
        stats.resist = round(stats.resist / 2, 2)
        stats.maxhp = int(stats.maxhp * 3 / 4)

    def choose_random_weight(self):
        return random.choice(self.weights)

    def scale_attribue_with_rarity(self, stat: int | float, name, rarity: str):
        multiplier = self.rarity_scaling[rarity]
        attribute_rarity_scaling = {
            "moves": lambda x: int(x + 1 * (multiplier - 1)),
            "critchance": lambda x: round(x * multiplier, 2),
            "critmult": lambda x: round(x + 1 * (multiplier - 1), 2),
            "attacks": lambda x: int(x + 1 * (multiplier - 1)),
            "multicast": lambda x: round(x * 1 + multiplier / 2, 2),
            "healing": lambda x: round(x * multiplier, 2)
        }
        return attribute_rarity_scaling[name](stat)

    # hp uses mult, resist and dodge should be altered
    def scale_base_stats_with_rarity(self, gear: Gear):
        multiplier = self.rarity_scaling[gear.rarity]

        for attr in [stat for stat in fields(type(gear.stats)) if stat.name != "bonus_stats"]:
            value = getattr(gear.stats, attr.name)
            if isinstance(value, int):
                value = int(value * multiplier)
            else:
                value = round((value * multiplier), 2)
            setattr(gear.stats, attr.name, value)

    def randomize_gear_stats(self, maxres, maxhp, maxdodge):
        resist = round(random.uniform(maxres / 5, maxres), 2)
        hp = random.randint(maxhp // 5, maxhp)
        dodge: float = round(random.uniform(maxdodge / 5, maxdodge), 2)
        # TODO: Bonus stats moves to loot gen
        return GearStatTable(resist, hp, dodge, BonusStatsTable())

    def generate_random_stats(self, gear_type):
        type_stat_randomizers = {
            HeadGear: self.randomize_gear_stats(0.1, 5, .05),
            ChestGear: self.randomize_gear_stats(0.2, 10, 0.1),
            HandGear: self.randomize_gear_stats(0.05, 5, 0.03),
            LegGear: self.randomize_gear_stats(0.1, 10, 0.05),
            FootGear: self.randomize_gear_stats(0.05, 5, 0.1)
        }
        return type_stat_randomizers[gear_type]

    def randomize_attribute_value(self, attribute: str):
        attribute_values = {
            "moves": random.randint(1, 2),
            "critchance": round(random.uniform(0.03, 0.12), 2),
            "critmult": round(random.uniform(0.05, 0.25), 2),
            "attacks": random.randint(1, 2),
            "multicast": round(random.uniform(0.02, 0.08), 2),
            "healing": round(random.uniform(0.08, 0.32), 2),
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
        excluded = ['name', 'emoji', 'rarity', 'value', 'stack_size', 'quantity', 'stats']
        gear_fields = [field.name for field in fields(gear_class)
                       if field.name not in excluded]

        return random.choice(gear_fields)

    def get_field_by_name(self, gear, field):
        return getattr(gear, field, None)

    def set_field_by_name_value(self, gear, field, value):
        setattr(gear, field, value)


class Loot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)

    async def generate_random_gear(self, player: PlayableCharacter):
        generator = LootGenerator(player.level, player.origin)
        randgear = generator.generate_loot()
        return randgear

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


async def setup(bot):
    await bot.add_cog(Loot(bot))


