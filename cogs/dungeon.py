import discord
from discord.ext import commands
from custom.playable_character import PlayableCharacter
import custom.stattable as sts
from items.weapons import Greatsword, Fists
from custom.combat.enemy import Enemy
from custom.combat.enemies import TrainingDummy, Wolf, Skeleton, Bandit, DarkMage, Golem
from custom.gear import Loadout
from custom.combat.barbarian.cooldowns import BarbarianCooldownInfo
from custom.combat.rogue.cooldowns import RogueCooldownInfo
from custom.stattable import Origin, Barbarian, Rogue, Wizard
import asyncio
from cogs.combat import CombatInstance
from cogs.database import Database


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)

    @discord.app_commands.command(name="dungeonmenu")
    async def send_test_dungeon_menu(self, interaction: discord.Interaction):
        encounter_names = {
            0: "TrainingRoom",
            1: "Wolf Den",
            2: "Bandit Camp",
        }
        view = DungeonView(interaction=interaction)
        await interaction.response.send_message("Dungeons\n\nSelect a Dungeon:", view=view)
        await view.wait()
        choice = view.choice
        if choice == -2:
            return
        enemies = self.get_enemy_list(choice)
        player = self.db.get_character(interaction.user.id)
        loadout = self.db.load_equipment(interaction.user.id)
        cooldown_indexes = self.db.get_cooldowns(interaction.user.id)
        cooldowns = self.get_cooldowns(player.origin, cooldown_indexes)
        instance = CombatInstance(interaction, [player], [loadout],[cooldowns], enemies)
        result = instance.combat()
        if result == -1:
            await interaction.edit_original_response(content="You Died.", view=None)
        elif result == 0:
            await interaction.edit_original_response(content="You Successfully Ran.", view=None)
        else:
            await interaction.edit_original_response(content=f"You Defeated {encounter_names[choice]}!", view=None)
            gold, xp = self.get_drop_results(enemies)
            self.db.add_gold(interaction.user.id, gold)
            self.db.add_xp(interaction.user.id, xp)
            player.gold += gold
            player.xp += xp
            await asyncio.sleep(4.0)
            await interaction.edit_original_response(content=f"Rewards\nGold: {gold}\nXP: {xp}", embed=None)
        await asyncio.sleep(4.0)
        await interaction.delete_original_response()

    def get_drop_results(self, enemies: list[Enemy]):
        gold = 0
        xp = 0

        for enemy in enemies:
            gold += enemy.drops.gold
            xp += enemy.drops.xp

        return gold, xp

    def get_enemy_list(self, choice: int):
        choices = {
            0: [TrainingDummy, TrainingDummy, TrainingDummy, TrainingDummy],
            1: [Wolf, Wolf],
            2: [Bandit, Bandit, Bandit],
        }
        return choices[choice]

    def get_cooldowns(self, playerclass: Origin, indexes: list[int]):
        origin_tables = {
            Barbarian: BarbarianCooldownInfo.cooldowns,
            Rogue: RogueCooldownInfo.cooldowns,
            Wizard: -1,
        }
        table = origin_tables[playerclass]
        cooldowns = []
        for i in indexes:
            if i != -1:
                cooldowns.append(table[i])
        return cooldowns

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


class ContinueView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.interaction: discord.Interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def continue_button(self, interaction: discord.Interaction, button):
        self.event.set()
        self.interaction = interaction

    async def wait(self):
        await self.event.wait()


class DungeonSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Training Room",
                description="Practice combat basics",
                value="0"
            ),
            discord.SelectOption(
                label="Wolf Den",
                description="Face wild wolves",
                value="1"
            ),
            discord.SelectOption(
                label="Bandit Camp",
                description="Fight dangerous bandits",
                value="2"
            )
        ]
        self.names = {
            0: "TrainingRoom",
            1: "Wolf Den",
            2: "Bandit Camp",
        }
        super().__init__(
            placeholder="Choose your dungeon...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.children[0].disabled = False
        selected = int(self.values[0])

        self.view.choice = selected
        self.placeholder = self.names[selected]
        await self.view.interaction.edit_original_response(view=self.view)
        await interaction.response.defer()


class DungeonView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction
        self.choice = -9
        self.event = asyncio.Event()
        self.add_item(DungeonSelect())

    @discord.ui.button(label="Proceed", style=discord.ButtonStyle.green, row=4, disabled=True, custom_id="proceed_button")
    async def proceed_button(self, interaction: discord.Interaction, button):
        self.event.set()
        await interaction.response.defer()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red, row=4)
    async def back_button(self, interaction: discord.Interaction, button):
        self.choice = -2
        self.event.set()
        await interaction.response.defer()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Dungeon(bot))


