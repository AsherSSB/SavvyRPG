import discord
from discord.ext import commands
import asyncio
from custom.playable_character import PlayableCharacter

class MainMenus(commands.Cog):
    def __init__(self, bot, user_character=None): 
        self.bot = bot
        self.user_character:PlayableCharacter = user_character

    async def send_main_menu(self, interaction:discord.Interaction):
        choices = ["Adventure", "Character", "Shop", "Social", "Tavern"]
        embeds = [None, CharacterEmbed(self.user_character), None, None, None]
        views = [None, None, None, None, None]
        embed = MainMenuEmbed()
        view = MainMenuButtons()
        await interaction.response.send_message("main menu", embed=embed, view=view)
        await view.wait()
        await interaction.edit_original_response(content=choices[view.choice], embed=embeds[view.choice], view=views[view.choice])
        await view.interaction.response.defer()


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
        self.add_field(name="Stats:", value=pc.stats)


async def setup(bot):
    await bot.add_cog(MainMenus(bot))