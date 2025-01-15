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

    @discord.app_commands.command(name="gearmenu")
    async def test_send_equip_slots_menu(self, interaction: discord.Interaction):
        await self.send_equip_slots_menu(interaction)

    async def send_equip_slots_menu(self, interaction: discord.Interaction):
        view = ButtonGearView(interaction)
        await interaction.response.send_message("Gear", view=view)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        else:
            loadout = self.db.load_equipment(interaction.user.id)
            inventory = self.db.load_inventory(interaction.user.id)
            interaction = await self.equip_item(view.interaction, loadout, inventory, view.choice)
            return await self.send_equip_slots_menu(interaction)

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
        if len(equippables) < 1:
            view = ContinueView()
            await interaction.response.send_message("You have no items of that kind to equip!", view=view)
            await view.wait()
            return await self.send_equip_slots_menu(view.interaction)
        # returns interaction back to main menus
        return await self.send_equip_menu(interaction, loadout, equippables, attr)

    async def send_equip_menu(self, interaction, loadout: Loadout, inventory: list[Item], slot: str):
        embed = InventoryEmbed(inventory=inventory)
        view = InventoryView(interaction=interaction, inventory=inventory, embed=embed)
        await interaction.response.send_message(content="Equippables", view=view, embed=embed)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        choice = view.choice
        interaction = view.interaction
        setattr(loadout, slot, inventory[choice])
        self.db.save_equipment(interaction.user.id, loadout)
        view = ContinueView()
        await interaction.response.send_message(f"Successfully equipped {inventory[choice].name}!", view=view)
        await view.wait()
        return view.interaction

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


class ContinueView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.interaction: discord.Interaction

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def continue_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(GearMenu(bot))


