import discord
from discord.ext import commands
import asyncio
from dataclasses import fields
from cogs.loot_randomizer import Loot
from cogs.database import Database


class Blacksmith(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.loot = Loot(self.bot)
        self.db = Database(self.bot)

    @discord.app_commands.command(name="sendblacksmith")
    async def sendmenutest(self, interaction: discord.Interaction):
        await self.send_blacksmith_menu(interaction)

    async def send_blacksmith_menu(self, interaction: discord.Interaction):
        view = BlacksmithView()
        await interaction.response.send_message("Blacksmith\nBuy and sell equipment and armor", view=view)
        await view.wait()
        if view.choice == -1:
            return view.interaction
        elif view.choice == 0:
            await view.interaction.response.defer()
            await self.send_buy_menu(interaction)
        # TODO: sell menu
        else:
            pass

    async def send_buy_menu(self, interaction: discord.Interaction):
        view = BuyView()
        await interaction.edit_original_response(content="Buy Menu\nBasic Chest: 80g", view=view)
        await view.wait()
        if view.choice == -1:
            await self.send_blacksmith_menu(view.interaction)
        elif view.choice == 0:
            player = self.db.get_character(view.interaction.user.id)
            inventory = self.db.load_inventory(view.interaction.user.id)
            if player.gold >= 80 and len(inventory) <= 25:
                player.gold -= 80
                self.db.add_gold(view.interaction.user.id, -80)
                gear = await self.loot.generate_random_gear(player)
                inventory.append(gear)
                self.db.save_inventory(view.interaction.user.id, inventory)
                content = []
                for field in fields(type(gear)):
                    # Skip private fields
                    if field.name.startswith('_'):
                        continue

                    value = getattr(gear, field.name)
                    content.append(f"{field.name}: {value}")
                formatted_content = "\n".join(content)
                interaction = view.interaction
                view = ContinueView()
                await interaction.response.send_message(f"Got Item!\n{formatted_content}", view=view)
                await view.wait()
                await view.interaction.response.send_message("Loading...")
                await self.send_buy_menu(view.interaction)
            elif player.gold < 80:
                interaction = view.interaction
                view = ContinueView()
                await interaction.response.send_message("You do not have enough gold for that", view=view)
                await view.wait()
                await view.interaction.response.send_message("Loading...")
                await self.send_buy_menu(view.interaction)
            else:
                interaction = view.interaction
                view = ContinueView()
                await interaction.response.send_message("Your inventory is full!", view=view)
                await view.wait()
                await view.interaction.response.send_message("Loading...")
                await self.send_buy_menu(view.interaction)

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


class BuyView(discord.ui.View):
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

    @discord.ui.button(label="Basic Chest", style=discord.ButtonStyle.green)
    async def buy_basic_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.choice = 0
        self.event.set()

    async def wait(self):
        await self.event.wait()


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

    @discord.ui.button(label="Sell", style=discord.ButtonStyle.green)
    async def sell_button(self, interaction: discord.Interaction, button):
        self.interaction = interaction
        self.choice = 1
        self.event.set()

    async def wait(self):
        await self.event.wait()


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
    await bot.add_cog(Blacksmith(bot))


