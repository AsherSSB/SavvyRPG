import discord
from discord.ext import commands
from custom.gearview import ButtonGearView


class GearMenu(commands.cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def send_gear_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Gear", view=view)
        await view.wait()


async def setup(bot):
    bot.add_cog(GearMenu(bot))
