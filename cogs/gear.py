import discord
from discord.ext import commands
from custom.gearview import ButtonGearView
from custom.gear import Loadout
import asyncio
from cogs.database import Database
from custom.base_items import Item
from custom.inventory import InventoryView, InventoryEmbed


class GearMenu(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = Database(self.bot)

    async def send_equip_slots_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Gear", view=view)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        else:
            interaction = view.interaction
            loadout = self.db.load_equipment(interaction.user.id)
            inventory = self.db.load_inventory(interaction.user.id)
            await self.equip_item(interaction, loadout, inventory, view.choice)

    async def equip_item(self, interaction: discord.Interaction, loadout: Loadout, inventory: list[Item], slot_index: int):
        slots = {
            0: "head",
            1: "chest",
            2: "hands",
            3: "legs",
            4: "feet",
            5: "weapon"
        }
        attr = slots[slot_index]
        gear = getattr(loadout, attr, None)
        equippables = [item for item in inventory if isinstance(item, type(gear))]
        # returns interaction back to main menus
        return await self.send_equip_menu(interaction.user.id, equippables)

    async def send_equip_menu(self, interaction, inventory: list[Item]):
        inventory = self.inventory
        embed = InventoryEmbed(inventory=inventory)
        view = InventoryView(interaction=interaction, inventory=inventory, embed=embed)
        await interaction.response.send_message(content="Equippables", view=view, embed=embed)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        # TODO: should instead equip the item and save to database with a success message
        await interaction.edit_original_response(content=view.choice, view=None, embed=None)

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(GearMenu(bot))


