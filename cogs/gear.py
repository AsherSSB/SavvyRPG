import discord
from discord.ext import commands
from custom.gearview import ButtonGearView
from custom.gear import Loadout
import asyncio
from cogs.database import Database
from custom.base_items import Item
from cogs.inventory import Inventory


class GearMenu(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = Database()

    async def send_gear_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Gear", view=view)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        # TODO: replace this with equip menu for selected equipment slot
        else:
            interaction = view.interaction
            loadout = self.db.load_equipment(interaction.user.id)
            inventory = self.db.load_inventory(interaction.user.id)

    async def send_equip_item_menu(self, interaction: discord.Interaction, loadout: Loadout, inventory: list[Item], slot_index: int):
        inv = Inventory(self.bot)
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

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


async def setup(bot):
    await bot.add_cog(GearMenu(bot))


