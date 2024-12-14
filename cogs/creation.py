import discord
from discord.ext import commands
from custom.database import Database
import asyncio

class Creator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()


    @discord.app_commands.command(name="entername")
    async def name_character(self, interaction:discord.Interaction):
        asshole = await self.send_text_modal(interaction, "Enter Character Name", "Character Name")
        await interaction.followup.send(f"{asshole}")


    @discord.app_commands.command(name="gender")
    async def set_gender(self, interaction:discord.Interaction):
        view = GenderView()
        await interaction.response.send_message("hi", view=view)
        await view.wait()
        await interaction.followup.send(f"{view.value}")


    async def send_text_modal(self, interaction:discord.Interaction, title, label):
        modal = SingleTextSubmission(title, label)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal.textinput.value


    async def cleanup(self):
        self.db.conn.close
        self.db.cur.close


    async def cog_unload(self):
        await self.cleanup()



# TODO: return submission interaction to continue character creation
class SingleTextSubmission(discord.ui.Modal):
    def __init__(self, title, label):
        super().__init__(title=title)
        self.textinput = discord.ui.TextInput(label=label, required=True)
        self.add_item(self.textinput)
        self.event = asyncio.Event()

    async def on_submit(self, interaction:discord.Interaction):
        await interaction.response.send_message("recieved")
        self.event.set()

    async def wait(self):
        await self.event.wait()


# TODO: return selection interaction to continue character creation
# TODO: add "Other" option leading to SingleTextSubmission
class GenderView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.event = asyncio.Event()

    @discord.ui.button(label="Male")
    async def male_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()
        self.value = "Male"
        self.event.set()
        self.stop()

    @discord.ui.button(label="Female")
    async def female_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()
        self.value = "Female"
        self.event.set()
        self.stop()

    @discord.ui.button(label="Non-Binary")
    async def nb_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()
        self.value = "Non-Binary"
        self.event.set()
        self.stop()
        
    @discord.ui.button(label="Other")
    async def other_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        modal = SingleTextSubmission("Gender Select", "Enter Gender")
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.value = modal.textinput.value
        self.event.set()
        self.stop()    

    async def wait(self):
        await self.event.wait()

        

async def setup(bot):
    await bot.add_cog(Creator(bot))

