import discord
from discord.ext import commands
from custom.inventory import InventoryView, InventoryEmbed
from cogs.database import Database


class Inventory(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = Database(bot=self.bot)
        self.inventory: list

    async def send_inventory_menu(self, interaction: discord.Interaction):
        inventory = self.inventory
        embed = InventoryEmbed(inventory=inventory)
        view = InventoryView(interaction=interaction, inventory=inventory, embed=embed)
        await interaction.response.send_message(content="Inventory", view=view, embed=embed)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        await interaction.edit_original_response(content=view.choice, view=None, embed=None)

    def set_entire_inventory(self, userid):
        self.inventory = self.db.load_inventory(userid)

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Inventory(bot))


