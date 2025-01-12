import discord
from discord.ext import commands

class Blacksmith(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(name="sendblacksmith")
    async def send_blacksmith_menu(self, interaction: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(Blacksmith(bot))


