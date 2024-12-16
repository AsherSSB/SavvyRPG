import discord
from discord.ext import commands
import asyncio
from custom.playable_character import PlayableCharacter

class MainMenus(commands.Cog):
    def __init__(self, bot, user_character=None): 
        self.bot = bot
        self.user_character:PlayableCharacter = user_character

    async def send_main_menu(self, interaction:discord.Interaction):
        embed = MainMenuEmbed()
        view = MainMenuButtons()
        await interaction.response.send_message("main menu", embed=embed, view=view)
        await view.wait()
        # TODO: may want to switch interaction here if timing out
        await view.interaction.response.defer()
        menus = {
            0: self.send_adventure_menu,
            1: self.send_character_menu,
            2: self.send_market_menu,
            3: self.send_social_menu,
            4: self.send_tavern_menu
        }
        # interaction not refreshed, edit only
        await menus[view.choice](interaction)

    async def send_adventure_menu(self, interaction:discord.Interaction):
        pass

    async def send_character_menu(self, interaction:discord.Interaction):
        embed = CharacterEmbed(self.user_character)
        view = CharacterView()
        await interaction.edit_original_response(content="Character", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)

    async def send_market_menu(self, interaction:discord.Interaction):
        pass

    async def send_social_menu(self, interaction:discord.Interaction):
        pass

    async def send_tavern_menu(self, interaction:discord.Interaction):
        pass


class MainMenuEmbed(discord.Embed):
    def __init__(self, *, title = "Savvy RPG", description = None):
        super().__init__(title=title, description=description, color=discord.Color(0x00ffff))
        self.add_field(name="Adventure", value="Quest to Complete, Chests to Loot, and Monsters to Slay", inline=True)
        self.add_field(name="Character", value="View Character Stats and Inventory", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Shop", value="Buy Items and Equipment", inline=True)
        self.add_field(name="Social", value="Add Friends, Manage Clan, and Join Groups", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Tavern", value="View Quests and Engage in Degeneracy", inline=True)


class MainMenuButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice:int = None
        self.interaction:discord.Interaction
        self.event = asyncio.Event()

    @discord.ui.button(label="Adventure", style=discord.ButtonStyle.primary)
    async def adventure_button(self, interaction:discord.Interaction, button):
        self.choice = 0
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Character", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction:discord.Interaction, button):
        self.choice = 1
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.success)
    async def shop_button(self, interaction:discord.Interaction, button):
        self.choice = 2
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Social", style=discord.ButtonStyle.danger)
    async def social_button(self, interaction:discord.Interaction, button):
        self.choice = 3
        self.interaction = interaction
        self.event.set()
    
    @discord.ui.button(label="Tavern", style=discord.ButtonStyle.primary)
    async def tavern_button(self, interaction:discord.Interaction, button):
        self.choice = 4
        self.interaction = interaction
        self.event.set() 

    async def wait(self):
        await self.event.wait()


class CharacterEmbed(discord.Embed):
    def __init__(self, pc:PlayableCharacter):
        super().__init__(color=discord.Color(0x00ffff), 
                         title=pc.name, 
                         description=f"{pc.gender} {pc.race} {pc.origin}")
        self.add_field(name=f"Level {pc.xp}", value=pc.xp)
        self.add_field(name="Stats:", value=pc.stats)


class NavigationMenuView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.choice:int
        self.interaction:discord.Interaction
        self.add_item(BackButton())

    async def wait(self):
            await self.event.wait()

class CharacterView(NavigationMenuView):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Gear", style=discord.ButtonStyle.success)
    async def navigate_gear(self, interaction:discord.Interaction, button):
        self.choice = 0
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.primary)
    async def navigate_inventory(self, interaction:discord.Interaction, button):
        self.choice = 1
        self.interaction = interaction
        self.event.set()


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Back")

    def callback(self, interaction):
        self.view.choice = -1
        self.view.interaction = interaction
        self.view.event.set()



async def setup(bot):
    await bot.add_cog(MainMenus(bot))