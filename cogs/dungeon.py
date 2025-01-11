import discord
from discord.ext import commands
from custom.playable_character import PlayableCharacter
import custom.stattable as sts
from items.weapons import Greatsword, Fists
from custom.combat.enemies import TrainingDummy, Wolf, Skeleton, Bandit, DarkMage, Golem
from custom.gear import Loadout
from custom.combat.barbarian.cooldowns import Cleave, Execute
import asyncio
from cogs.combat import CombatInstance
from cogs.database import Database


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self.bot)

    @discord.app_commands.command(name="dungeonmenu")
    async def send_test_dungeon_menu(self, interaction: discord.Interaction):
        view = DungeonView(interaction=interaction)
        await interaction.response.send_message("Dungeons\n\nSelect a Dungeon:", view=view)
        await view.wait()
        choice = view.choice
        await interaction.edit_original_response(content=choice)
        await asyncio.sleep(3.0)
        await interaction.delete_original_response()
        if choice == -2:
            return
        # TODO: get enemy list based on choice
        player = self.db.get_character(interaction.user.id)
        loadout = self.db.load_equipment(interaction.user.id)
        cooldown_indexes = self.db.get_cooldowns(interaction.user.id)
        # TODO: replace indexes with classes
        cooldowns = []
        instance = CombatInstance(interaction, [player], [loadout],[cooldowns], [enemy])

    async def start_combat(self, interaction:discord.Interaction):
        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        testwep = Greatsword()
        enemy = Wolf()

        loadout = Loadout(None, None, None, None, None, [testwep])

        interaction = await self.send_testing_view(interaction)
        instance = CombatInstance(interaction, [self.pc], [loadout],[[Cleave, Execute]], [enemy])
        result = await instance.combat()
        if result == -1:
            await interaction.edit_original_response(content="You Died.", view=None)
        elif result == 0:
            await interaction.edit_original_response(content="You Successfully Ran.", view=None)
        else:
            await interaction.edit_original_response(content=f"You Defeated {enemy.name}!", view=None)

        await asyncio.sleep(4.0)
        await interaction.edit_original_response(content=f"Rewards\nGold: {enemy.drops.gold}\nXP: {enemy.drops.xp}", embed=None)
        await asyncio.sleep(4.0)
        await interaction.delete_original_response()

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


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


