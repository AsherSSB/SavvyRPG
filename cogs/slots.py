import discord
from discord.ext import commands
import random
import asyncio

class Slots(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.reel = [":cherries:", ":grapes:", ":lemon:", ":bell:", ":seven:"]
        self.probs = [.25, .25, .25, .2, .05]
        self.pay = [10, 50, 100, 500, 20000]
        random.seed()

    @discord.app_commands.command(name="spin")
    async def spin(self, interaction:discord.Interaction):
        await self.play_slots(interaction)
        
    async def play_slots(self, interaction:discord.Interaction):
        await self.flicker(interaction)
        view = Again()
        await interaction.edit_original_response(view=view)
        await view.wait()
        if view.play_again:
            await interaction.delete_original_response()
            interaction = view.interaction
            await self.play_slots(interaction)
        else:
            await interaction.delete_original_response()
            await view.interaction.response.defer()
            

    async def flicker(self, interaction:discord.Interaction):
        i = 0
        res = self.spin_reel()
        end = f"Slots\n{res[0]}{res[1]}{res[2]}"
        if self.all_elements_same(res):
            end += "\nYou Win!"
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

    def spin_reel(self):
        return random.choices(self.reel, weights=self.probs, k=3)

    def all_elements_same(self, lst):
        return all(x == lst[0] for x in lst)

    def pick_random_element(self):
        return random.choice(self.reel)
    

class Again(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.play_again:bool
        self.interaction:discord.Interaction
        
    @discord.ui.button(label="Spin")
    async def spin_again(self, interaction:discord.Interaction, button):
        self.play_again = True
        self.event.set()
        self.interaction = interaction

    @discord.ui.button(label="Exit")
    async def exit(self, interaction:discord.Interaction, button):
        self.play_again = False
        self.event.set()
        self.interaction = interaction

    async def wait(self):
        await self.event.wait()

async def setup(bot):
    await bot.add_cog(Slots(bot))