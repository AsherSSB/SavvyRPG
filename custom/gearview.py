import discord
import asyncio

class GearSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(max_values=1)
        self.add_option(label="Head", value="0", emoji="🧢")
        self.add_option(label="Chest", value="1", emoji="👕")
        self.add_option(label="Hands", value="2", emoji="🧤")
        self.add_option(label="Legs", value="3", emoji="👖")
        self.add_option(label="Feet", value="4", emoji="👢")

    async def callback(self, interaction):
        self.view.choice = int(self.values[0])
        await interaction.response.defer()
        self.view.event.set()


class ButtonGearView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.choice: int
        self.event = asyncio.Event()
        self.method = 0
        self.style = 0
        self.labels = ["Head","Chest","Hands","Legs","Feet"]
        self.buttons = []
        self.select: discord.SelectMenu = GearSelect()

        button_dict = [
            {"label": "Head", "style": discord.ButtonStyle.gray, "emoji": "🧢"}, 
            {"label": "Chest", "style": discord.ButtonStyle.gray, "emoji": "👕"},
            {"label": "Hands", "style": discord.ButtonStyle.gray, "emoji": "🧤"},
            {"label": "Legs", "style": discord.ButtonStyle.gray, "emoji": "👖"}, 
            {"label": "Feet", "style": discord.ButtonStyle.gray, "emoji": "👢"}
        ]
        
        # Create and add buttons
        for i, btn in enumerate(button_dict):
            button = discord.ui.Button(
                label=btn["label"],
                style=btn["style"],
                emoji=btn.get("emoji"),
                row=0
            )
            button.callback = self.create_callback(i)
            self.buttons.append(button)
        
        for button in self.buttons:
            self.add_item(button)

    def create_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            self.choice = choice
            await interaction.response.defer()
            self.event.set()
        return callback
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.red, row=2)
    async def back_button(self, interaction: discord.Interaction, button):
        self.choice = -1
        await interaction.response.defer()
        self.event.set()

    @discord.ui.button(label="Swap Select Method", style=discord.ButtonStyle.green, row=2)
    async def swap_method_button(self, interaction: discord.Interaction, button):
        if self.method == 0:
            self.method = 1
            await self.swap_to_select()
        else:
            self.method = 0
            await self.swap_to_buttons()
        await interaction.response.defer()

    @discord.ui.button(label="Swap Styles", style=discord.ButtonStyle.green, row=2)
    async def swap_style_button(self, interaction: discord.Interaction, button):
        if self.style == 0:
            self.style = 1
            await self.remove_button_text()
            await self.remove_select_text()
        else:
            self.style = 0
            await self.add_button_text()
            await self.add_select_text()
        await interaction.response.defer()
        await self.interaction.edit_original_response(view=self)

    async def add_select_text(self):
        for i, option in enumerate(self.select.options):
            option.label = self.labels[i]

    async def add_button_text(self):
        for i, button in enumerate(self.buttons):
            button.label = self.labels[i]
    
    async def remove_button_text(self):
        for button in self.buttons:
            button.label = ""

    async def remove_select_text(self):
        for option in self.select.options:
            option.label = "⠀"

    async def swap_to_buttons(self):
        self.remove_item(self.select)
        for button in self.buttons:
            self.add_item(button)
        await self.interaction.edit_original_response(view=self)

    async def swap_to_select(self):
        for button in self.buttons:
            self.remove_item(button)
        self.add_item(self.select)
        await self.interaction.edit_original_response(view=self)

    async def wait(self):
        await self.event.wait()
