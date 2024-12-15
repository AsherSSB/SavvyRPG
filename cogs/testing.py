import discord
from discord.ext import commands
from custom.weapons import Sword, Shield

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="statprint")
    async def stattest(self, interaction:discord.Interaction):
        sword = Sword()
        shield = Shield(10)
        await interaction.response.send_message(f"{sword}\n{shield}")


async def setup(bot):
    await bot.add_cog(Testing(bot))