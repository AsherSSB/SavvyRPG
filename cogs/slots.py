import discord
from discord.ext import commands
import random
import asyncio


# TODO: detect timeout on spin
class Slots(commands.Cog):
    def __init__(self, bot, gold=0):
        super().__init__()
        self.bot = bot
        self.reel = [":cherries:", ":grapes:", ":lemon:", ":bell:", ":seven:"]
        self.probs = [.25, .25, .25, .2, .05]
        self.pay = [10, 50, 100, 500, 20000]
        self.gold = gold
        self.interaction:discord.Interaction
        random.seed()

    async def spin(self, interaction:discord.Interaction):
        view = BetView()
        await interaction.response.send_message(content=f"Your Gold: {self.gold}\nSpins Cost 10 Gold Each\nCherries Pay 1x, Grapes Pay 5x, Lemons Pay 10x, Bells Pay 50x, and Sevens Pay 2000x", view=view)
        await view.wait()
        interaction = view.interaction
        if view.choice == -1:
            self.interaction = interaction
            return self.gold
        elif view.choice == 0:
            mult = await self.flicker(interaction)
            self.gold += 10 * mult
            view = BackView()
            await interaction.edit_original_response(view=view)
            await view.wait()
            interaction = view.interaction
            await self.spin(interaction)
        else:
            self.gold += 100
            await self.spin(interaction)

        return self.gold

    async def flicker(self, interaction:discord.Interaction):
        i = 0
        res = self.spin_reel()
        end = f"Slots\n{res[0]}{res[1]}{res[2]}"
        multiplier = -1
        if self.all_elements_same(res):
            end += "\nYou Win!"
            mults = {
                ":cherries:": 1,
                ":grapes:": 5,
                ":lemon:": 10,
                ":bell:": 50,
                ":seven:": 2000
            }
            multiplier = mults[res[0]]
        one = self.pick_random_element()
        two = self.pick_random_element()
        three = self.pick_random_element()
        content = f"Slots\n{one}{two}{three}"
        await interaction.response.send_message(content)
        while i < 2:
            one = self.pick_random_element()
            two = self.pick_random_element()
            three = self.pick_random_element()
            content = f"Slots\n{one}{two}{three}"
            await interaction.edit_original_response(content=content)
            i += 1
        while i < 4:
            two = self.pick_random_element()
            three = self.pick_random_element()
            content = f"Slots\n{res[0]}{two}{three}"
            await interaction.edit_original_response(content=content)
            i += 1
        while i < 7:
            three = self.pick_random_element()
            content = f"Slots\n{res[0]}{res[1]}{three}"
            await interaction.edit_original_response(content=content)
            i += 1
        await interaction.edit_original_response(content=end)
        return multiplier

    def spin_reel(self):
        return random.choices(self.reel, weights=self.probs, k=3)

    def all_elements_same(self, lst):
        return all(x == lst[0] for x in lst)

    def pick_random_element(self):
        return random.choice(self.reel)


class BetView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.interaction:discord.Interaction
        self.event = asyncio.Event()
        self.choice:int
        self.add_item(BackButton())

    @discord.ui.button(label="Spin", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction:discord.Interaction, button):
        self.choice = 0
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Give Money", style=discord.ButtonStyle.blurple)
    async def money_button(self, interaction:discord.Interaction, button):
        self.choice = 1
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="Back")

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = -1
        self.view.interaction = interaction
        self.view.event.set()


class BackView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.interaction:discord.Interaction
        self.event = asyncio.Event()
        self.choice:int
        self.add_item(BackButton())

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Slots(bot))


