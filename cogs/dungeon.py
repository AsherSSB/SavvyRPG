import discord
from discord.ext import commands
from custom.playable_character import PlayableCharacter
import custom.stattable as sts
from items.weapons import Greatsword, Fists
from custom.combat.enemies import TrainingDummy, Wolf, Skeleton, Bandit, DarkMage, Golem
from custom.gear import Loadout
from custom.combat.barbarian.cooldowns import Cleave, Execute
import asyncio
from custom.combat import CombatInstance


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def test_combat(self, interaction:discord.Interaction):
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


async def setup(bot):
    await bot.add_cog(Dungeon(bot))


