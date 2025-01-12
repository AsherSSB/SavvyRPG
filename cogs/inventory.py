import discord
from discord.ext import commands
from custom.inventory import InventoryView, InventoryEmbed


class Inventory(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.app_commands.command(name="sendinv")
    async def send_inventory_menu(self, interaction: discord.Interaction):
        view = InventoryView
        embed = InventoryEmbed

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Inventory(bot))


