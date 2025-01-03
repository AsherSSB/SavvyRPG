import discord
from discord.ext import commands
import asyncio
from custom.playable_character import PlayableCharacter
from cogs.creation import Creator
from cogs.blackjack import Blackjack
from cogs.database import Database
from cogs.slots import Slots

UNDER_CONSTRUCTION:str = "This area is still under construction. Come back later when it is finished!"


class MainMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_character:PlayableCharacter
        self.db = Database(self.bot)

    @discord.app_commands.command(name="playsavvy")
    async def initialize_game(self, interaction:discord.Interaction):
        await self.login(interaction)

    async def login(self, interaction:discord.Interaction):
        login = Creator(self.bot)
        self.user_character = await login.login(interaction)
        interaction = login.interaction
        await interaction.response.send_message(content="Loading...")
        await self.send_main_menu(interaction)

    async def send_main_menu(self, interaction:discord.Interaction):
        embed = MainMenuEmbed()
        view = MainMenuButtons()
        await interaction.edit_original_response(content="main menu", embed=embed, view=view)
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
        if view.choice == -1:
            await self.send_main_menu(interaction)
        else:
            await self.send_under_construction(interaction)
            await self.send_adventure_menu(interaction)

    async def send_character_menu(self, interaction:discord.Interaction):
        embed = CharacterEmbed(self.user_character)
        view = CharacterView()
        await interaction.edit_original_response(content="Character", embed=embed, view=view)
        await view.wait()
        if view.choice == -1:
            await view.interaction.response.defer()
            await self.send_main_menu(interaction)
        if view.choice == 2:
            await interaction.delete_original_response()
            interaction = view.interaction
            await self.confirm_character_deletion(interaction)
        else:
            await view.interaction.response.defer()
            await self.send_under_construction(interaction)
            await self.send_character_menu(interaction)

    async def confirm_character_deletion(self, interaction:discord.Interaction):
        name = self.user_character.name.upper()
        modal = SingleTextSubmission("ARE YOU SURE?", f"Type \"{name}\" and submit to delete character")
        await interaction.response.send_modal(modal)
        try:
            await asyncio.wait_for(modal.wait(), timeout=20.0)
            interaction = modal.interaction

            if modal.textinput.value == name:
                await self.db.delete_character(interaction)
            else:
                await interaction.response.send_message("Names do Not Match, Returning to Character Menu")
                await asyncio.sleep(4)
                await self.send_character_menu(interaction)
        except asyncio.TimeoutError:
            view = PlaceholderView()
            followup = await interaction.followup.send("Deletion Timed Out", view=view, ephemeral=True)
            await view.wait()
            await followup.delete()
            interaction = view.interaction
            await interaction.response.send_message("Loading...")
            await self.send_character_menu(interaction)

    async def send_market_menu(self, interaction:discord.Interaction):
        embed = MarketEmbed()
        view = MarketView()
        await interaction.edit_original_response(content="Market", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        if view.choice == -1:
            await self.send_main_menu(interaction)
        else:
            await self.send_under_construction(interaction)
            await self.send_market_menu(interaction)

    async def send_social_menu(self, interaction:discord.Interaction):
        embed = SocialEmbed()
        view = SocialView()
        await interaction.edit_original_response(content="Social", embed=embed, view=view)
        await view.wait()
        await view.interaction.response.defer()
        if view.choice == -1:
            await self.send_main_menu(interaction)
        else:
            await self.send_under_construction(interaction)
            await self.send_social_menu(interaction)

    async def send_tavern_menu(self, interaction:discord.Interaction):
        activities = {
            2: self.sendto_blackjack,
            3: self.sendto_slots,
        }
        embed = TavernEmbed()
        view = TavernView()
        await interaction.edit_original_response(content="Tavern", embed=embed, view=view)
        await view.wait()

        if view.choice in activities:
            await activities[view.choice](interaction=view.interaction)
        elif view.choice == -1:
            await view.interaction.response.defer()
            await self.send_main_menu(interaction)
        else:
            await view.interaction.response.defer()
            await self.send_under_construction(interaction)
            await self.send_tavern_menu(interaction)

    async def sendto_blackjack(self, interaction:discord.Interaction):
        blackjack = Blackjack(self.bot, self.user_character.gold)
        finishing_gold = await blackjack.play_blackjack(interaction)
        self.user_character.gold = finishing_gold
        self.db.set_gold(interaction.user.id, finishing_gold)
        interaction = blackjack.interaction
        await interaction.response.send_message("Loading...")
        await self.send_tavern_menu(interaction)

    async def sendto_slots(self, interaction:discord.Interaction):
        slots = Slots(self.bot, self.user_character.gold)
        end_gold = await slots.spin(interaction)
        self.user_character.gold = end_gold
        self.db.set_gold(interaction.user.id, end_gold)
        interaction = slots.interaction
        await interaction.response.send_message("Loading...")
        await self.send_tavern_menu(interaction)

    async def send_under_construction(self, interaction:discord.Interaction):
        view = PlaceholderView()
        await interaction.edit_original_response(content=UNDER_CONSTRUCTION, view=view, embed=None)
        await view.wait()
        await view.interaction.response.defer()

    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close

    async def cog_unload(self):
        await self.cleanup()


class MainMenuEmbed(discord.Embed):
    def __init__(self, *, title="Savvy RPG", description="Pre-Alpha v0.0.6: Now with 2 dimentional combat!"):
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
        self.add_field(name=f"Level {pc.level}", value=f"Xp: {pc.level_progress()} / {pc.xp_for_next_level()}\nGold: {pc.gold}g")
        self.add_field(name="Stats:", value=pc.stats)


class CharacterView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(NavigationMenuButton("Gear", discord.ButtonStyle.success, 0))
        self.add_item(NavigationMenuButton("Inventory", discord.ButtonStyle.primary, 1))
        self.add_item(NavigationMenuButton("Delete Character", discord.ButtonStyle.danger, 2))
        self.add_item(BackButton())


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Back")

    async def callback(self, interaction: discord.Interaction):
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

    async def callback(self, interaction):
        self.view.choice = self.choice
        self.view.interaction = interaction
        self.view.event.set()


class PlaceholderView(NavigationMenuView):
    def __init__(self):
        super().__init__()
        self.add_item(BackButton())


class SingleTextSubmission(discord.ui.Modal):
    def __init__(self, title, label):
        super().__init__(title=title)
        self.textinput = discord.ui.TextInput(label=label, required=True)
        self.add_item(self.textinput)
        self.event = asyncio.Event()
        self.interaction:discord.Interaction

    async def on_submit(self, interaction:discord.Interaction):
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(MainMenus(bot))


