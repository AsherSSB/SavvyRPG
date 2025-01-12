import discord
from discord.ext import commands
import asyncio

class Blacksmith(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(name="sendblacksmith")
    async def send_blacksmith_menu(self, interaction: discord.Interaction):
        view = BlacksmithView()
        await interaction.response.send_message("Blacksmith\n\nBuy and sell equipment and armor", view=view)
        await view.wait()
        await interaction.edit_original_response(content=view.choice, view=discord.utils.MISSING)

class BlacksmithView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice: int
        self.interaction: discord.Interaction
        self.event = asyncio.Event()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red)
    async def back_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.choice = -1
        self.event.set()

    @discord.ui.button(label="Buy", style=discord.ButtonStyle.green)
    async def buy_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.choice = 0
        self.event.set()

    @discord.ui.button(lable="Sell", style=discord.ButtonStyle.green)
    async def sell_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.choice = 1
        self.event.set()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Blacksmith(bot))


