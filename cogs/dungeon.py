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


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="dungeonmenu")
    async def send_test_dungeon_menu(self, interaction: discord.Interaction):
        view = DungeonView()
        await interaction.response.send_message("hello", view=view)
        await view.wait()
        await interaction.edit_original_response(content=view.choice)
        await asyncio.sleep(3.0)
        await interaction.delete_original_response()

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


class DungeonView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice = 0
        self.event = asyncio.Event()

    @discord.ui.button(label="Proceed", style=discord.ButtonStyle.green)
    async def proceed_button(self, interaction: discord.Interaction, button):
        self.choice = 1
        self.event.set()
        await interaction.response.defer()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Dungeon(bot))


