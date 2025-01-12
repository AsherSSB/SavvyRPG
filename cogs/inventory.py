import discord
from discord.ext import commands
from custom.inventory import InventoryView, InventoryEmbed
from cogs.database import Database


class Inventory(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = Database(bot=self.bot)

    @discord.app_commands.command(name="sendinv")
    async def send_inventory_menu(self, interaction: discord.Interaction):
        inventory = self.db.load_inventory(interaction.user.id)
        embed = InventoryEmbed(inventory=inventory)
        view = InventoryView(interaction=interaction, inventory=inventory, embed=embed)
        await interaction.response.send_message(content="Inventory", view=view, embed=embed)
        await view.wait()
        await interaction.edit_original_response(content=view.choice, view=None, embed=None)

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(Inventory(bot))


