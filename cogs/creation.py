import discord
from discord.ext import commands
from cogs.database import Database
import asyncio
import custom.stattable as origins
import custom.playable_character as pc

class Creator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database(bot=self.bot)
        self.interaction:discord.Interaction

    async def login(self, interaction:discord.Interaction):
        if self.db.user_exists(interaction.user.id):
            user_character = self.db.get_character(interaction.user.id)
            self.interaction = interaction
            return user_character
        else:
            return await self.create_character(interaction)

    async def create_character(self, interaction:discord.Interaction):
        confirmed = False
        while not confirmed:
            name = await self.name_character(interaction=interaction)
            view = ConfirmationView()
            followup = await interaction.followup.send(content=f"Name Character: \"{name}\"?", view=view)
            await view.wait()
            await followup.delete()
            interaction = view.interaction
            confirmed = view.confirmed
        
        confirmed = False
        while not confirmed:
            gender = await self.set_gender(interaction)
            view = ConfirmationView()
            await interaction.delete_original_response()
            followup = await interaction.followup.send(content=f"Set Gender: \"{gender}\"?", view=view)
            await view.wait()
            await followup.delete()
            interaction = view.interaction
            confirmed = view.confirmed

        confirmed = False
        while not confirmed:
            view = RaceView()
            await interaction.response.send_message(content="Select Race:", view=view)
            await view.wait()
            selected_race = view.race
            await view.interaction.response.defer()
            conview = ConfirmationView()
            await interaction.edit_original_response(content=selected_race.description, view=conview)
            await conview.wait()
            await interaction.delete_original_response()
            confirmed = conview.confirmed
            interaction = conview.interaction

        confirmed = False
        while not confirmed:
            view = OriginView()
            await interaction.response.send_message(content="Select Class:", view=view)
            await view.wait()
            selected_origin = view.origin
            await view.interaction.response.defer()
            conview = ConfirmationView()
            await interaction.edit_original_response(content=selected_origin.description, view=conview)
            await conview.wait()
            await interaction.delete_original_response()
            confirmed = conview.confirmed
            interaction = conview.interaction

        new_character = pc.PlayableCharacter(name, gender, selected_race, selected_origin)
        confirmed = False
        # TODO: allow user to change aspects of their character
        while not confirmed:
            view = ConfirmationView()
            await interaction.response.send_message(new_character, view=view)
            await view.wait()
            await interaction.delete_original_response()
            confirmed = view.confirmed
            interaction = view.interaction

        self.db.add_character(interaction.user.id, new_character)
        self.interaction = interaction
        return new_character

    async def name_character(self, interaction:discord.Interaction):
        name = await self.send_text_modal(interaction, "Enter Character Name", "Character Name")
        return name

    async def set_gender(self, interaction:discord.Interaction):
        view = GenderView()
        await interaction.response.send_message("Select Gender", view=view)
        await view.wait()
        return view.value

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
        await interaction.response.defer()
        self.event.set()

    async def wait(self):
        await self.event.wait()


# TODO: return selection interaction to continue character creation
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


class ConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.confirmed:bool
        self.event = asyncio.Event()
        self.interaction:discord.Interaction
        
    @discord.ui.button(label="Confirm")
    async def confirm_button(self, interaction:discord.Interaction, button):
        self.confirmed = True
        self.event.set()
        self.interaction = interaction 
        self.stop()

    @discord.ui.button(label="Cancel")
    async def cancel_button(self, interaction:discord.Interaction, button):
        self.confirmed = False
        self.event.set()
        self.interaction = interaction
        self.stop

    async def wait(self):
        await self.event.wait()


class OriginView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.origin = None
        self.event = asyncio.Event()
        self.interaction:discord.Interaction

    @discord.ui.button(label="Nomad")
    async def nomad_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Nomad()
        self.event.set()
        self.interaction = interaction

    @discord.ui.button(label="Barbarian")
    async def barb_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Barbarian()
        self.event.set()
        self.interaction = interaction

    @discord.ui.button(label="Bard")
    async def bard_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Bard()
        self.event.set()
        self.interaction = interaction

    @discord.ui.button(label="Rogue")
    async def rogue_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Rogue()
        self.event.set()
        self.interaction = interaction
    
    @discord.ui.button(label="Ranger")
    async def ranger_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Ranger()
        self.event.set()
        self.interaction = interaction

    @discord.ui.button(label="Wizard")
    async def wizard_button(self, interaction:discord.Interaction, button):
        self.origin = origins.Wizard()
        self.event.set()
        self.interaction = interaction

    async def wait(self):
        await self.event.wait()


class RaceView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.race = None
        self.event = asyncio.Event()
        self.interaction:discord.Interaction

    @discord.ui.button(label="Human")
    async def pick_human(self, interaction:discord.Interaction, button):
        self.race = origins.Human()
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="High Elf")
    async def pick_highelf(self, interaction:discord.Interaction, button):
        self.race = origins.HighElf()
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Dark Elf")
    async def pick_darkelf(self, interaction:discord.Interaction, button):
        self.race = origins.DarkElf()
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Dwarf")
    async def pick_dwarf(self, interaction:discord.Interaction, button):
        self.race = origins.Dwarf()
        self.interaction = interaction
        self.event.set()

    @discord.ui.button(label="Orc")
    async def pick_orc(self, interaction:discord.Interaction, button):
        self.race = origins.Orc()
        self.interaction = interaction
        self.event.set()
    
    @discord.ui.button(label="Fairy")
    async def pick_fairy(self, interaction:discord.Interaction, button):
        self.race = origins.Fairy()
        self.interaction = interaction
        self.event.set()
    
    @discord.ui.button(label="Damned")
    async def pick_damned(self, interaction:discord.Interaction, button):
        self.race = origins.Damned()
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()


async def setup(bot):
    await bot.add_cog(Creator(bot))

