import discord
from discord.ext import commands
from custom.gearview import ButtonGearView
import asyncio


class GearMenu(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def send_gear_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Gear", view=view)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        # TODO: replace this with equip menu for selected equipment slot
        else:
            await interaction.edit_original_response(content=view.choice, view=None)
            await asyncio.sleep(3.0)
            await interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(GearMenu(bot))
