import discord
from discord.ext import commands


class Inventory(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(name="sendinv")
    async def send_inventory_menu(self, interaction: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(Inventory(bot))


