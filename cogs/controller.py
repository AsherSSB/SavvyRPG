import discord
from discord.ext import commands

class Controller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @discord.app_commands.command(name="bro")
    async def testcommand(self, interaction:discord.Interaction):
        await interaction.response.send_message("Hello Bro!")


async def setup(bot):
    await bot.add_cog(Controller(bot))

