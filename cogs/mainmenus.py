import discord
from discord.ext import commands
import asyncio
from custom.playable_character import PlayableCharacter
from cogs.creation import Creator

class MainMenus(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.user_character:PlayableCharacter


    @discord.app_commands.command(name="playsavvy")
    async def login(self, interaction:discord.Interaction):
        login = Creator(self.bot)
        self.user_character = await login.login(interaction)
        interaction = login.interaction
        await self.send_main_menu(interaction)

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
        embed = AdventureEmbed()
        view = AdventureView()
        await interaction.edit_original_response(content="Adventure", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)

    async def send_character_menu(self, interaction:discord.Interaction):
        embed = CharacterEmbed(self.user_character)
        view = CharacterView()
        await interaction.edit_original_response(content="Character", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)

    async def send_market_menu(self, interaction:discord.Interaction):
        embed = MarketEmbed()
        view = MarketView()
        await interaction.edit_original_response(content="Market", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)

    async def send_social_menu(self, interaction:discord.Interaction):
        embed = SocialEmbed()
        view = SocialView()
        await interaction.edit_original_response(content="Social", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)

    async def send_tavern_menu(self, interaction:discord.Interaction):
        embed = TavernEmbed()
        view = TavernView()
        await interaction.edit_original_response(content="Tavern", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        await interaction.edit_original_response(content=view.choice, embed=None, view=None)
        


class MainMenuEmbed(discord.Embed):
    def __init__(self, *, title = "Savvy RPG", description = None):
        super().__init__(title=title, description=description, color=discord.Color(0x00ffff))
        self.add_field(name="Adventure", value="Quest to Complete, Chests to Loot, and Monsters to Slay", inline=True)
        self.add_field(name="Character", value="View Character Stats and Inventory", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Market", value="Craft, Buy, Sell, and Unbox Equipment", inline=True)
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

    @discord.ui.button(label="Market", style=discord.ButtonStyle.success)
    async def market_button(self, interaction:discord.Interaction, button):
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




class NavigationMenuView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.choice:int
        self.interaction:discord.Interaction

    async def wait(self):
            await self.event.wait()


class AdventureEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=discord.Color(0x00ffff),
                         title="Adventure",
                         description="Go on a Journey for The and Riches!")
        self.add_field(name="Campaign", value="Play Through the Story of Aether", inline=True)
        self.add_field(name="Dungeons", value="Fight Through Dungeons Solo or With a Party", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Infinity Tower", value="Scale The Tower, Increased Loot The Higher You Get", inline=True)
        self.add_field(name="World Boss", value="Help The Other Champions of Aether Slay The World Boss", inline=True)


class AdventureView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Campaign", discord.ButtonStyle.success, 0))
        self.add_item(NavigationMenuButton("Dungeons", discord.ButtonStyle.danger, 1))
        self.add_item(NavigationMenuButton("Infinity Tower", discord.ButtonStyle.primary, 2))
        self.add_item(NavigationMenuButton("World Boss", discord.ButtonStyle.secondary, 3))
        self.add_item(BackButton())


class CharacterEmbed(discord.Embed):
    def __init__(self, pc:PlayableCharacter):
        super().__init__(color=discord.Color(0x00ffff), 
                         title=pc.name, 
                         description=f"{pc.gender} {pc.race} {pc.origin}")
        self.add_field(name=f"Level {pc.xp}", value=pc.xp)
        self.add_field(name="Stats:", value=pc.stats)


class CharacterView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Gear", discord.ButtonStyle.success, 0))
        self.add_item(NavigationMenuButton("Inventory", discord.ButtonStyle.primary, 1))
        self.add_item(BackButton())


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Back")

    def callback(self, interaction):
        self.view.choice = -1
        self.view.interaction = interaction
        self.view.event.set()


class MarketEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=discord.Color(0x00ffff), 
                         title="Market",
                         description="Visit Merchants to Acquire and Upgrade Gear")
        self.add_field(name="Blacksmith", value="Buy, Sell, Craft, and Upgrade Armor and Weapons of War", inline=True)
        self.add_field(name="Enchantress", value="Buy and Sell Magical Items, Enchant Gear, and Socket Gems", inline=True)


class MarketView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Blacksmith", discord.ButtonStyle.green, 0))
        self.add_item(NavigationMenuButton("Enchantress", discord.ButtonStyle.blurple, 1))
        self.add_item(BackButton())


class SocialEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=discord.Color(0x00ffff),
                         title="Social",
                         description="Manage Friends, Party, and Clan")
        self.add_field(name="Party", value="View and Manage Current Party", inline=True)
        self.add_field(name="Friends", value="Manage Friends and View Profiles", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Clan", value="Join or View Your Clan", inline=True)


class SocialView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Party", discord.ButtonStyle.blurple, 0))
        self.add_item(NavigationMenuButton("Friends", discord.ButtonStyle.green, 1))
        self.add_item(NavigationMenuButton("Clan", discord.ButtonStyle.gray, 2))
        self.add_item(BackButton())


class TavernEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=discord.Color(0x00ffff), 
                         title="Tavern",
                         description="View Your Quests or Stay Awhile if You're Feeling Lucky")
        self.add_field(name="Weeklies", value="View Your Weekly Quests", inline=True)
        self.add_field(name="Dailies", value="View Your Daily Quests", inline=True)
        self.add_field(name="\u200b", value="\u200b", inline=False)
        self.add_field(name="Blackjack", value="A Sum of 21 is All You Need to Win Some Coin", inline=True)
        self.add_field(name="Slots", value="Spin Some Reels for a Chance to Win Big", inline=True)


class TavernView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Weeklies", discord.ButtonStyle.blurple, 0))
        self.add_item(NavigationMenuButton("Dailies", discord.ButtonStyle.blurple, 1))
        self.add_item(NavigationMenuButton("Blackjack", discord.ButtonStyle.gray, 2))
        self.add_item(NavigationMenuButton("Slots", discord.ButtonStyle.green, 3))
        self.add_item(BackButton())


class NavigationMenuButton(discord.ui.Button):
    def __init__(self, label, style, choice):
        super().__init__(style=style, label=label)
        self.choice = choice

    def callback(self, interaction):
        self.view.choice = self.choice
        self.view.interaction = interaction
        self.view.event.set()


async def setup(bot):
    await bot.add_cog(MainMenus(bot))