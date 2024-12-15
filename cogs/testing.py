import discord
from discord.ext import commands
from custom.weapons import Sword, Shield
from custom.stattable import Nomad, Barbarian

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="nomadtest")
    async def nomadtest(self, interaction:discord.Interaction):
        nomad = Nomad()
        await interaction.response.send_message(f"{nomad}")

    @discord.app_commands.command(name="barbtest")
    async def nomadtest(self, interaction:discord.Interaction):
        nomad = Barbarian()
        await interaction.response.send_message(f"{nomad}")
    

async def setup(bot):
    await bot.add_cog(Testing(bot))