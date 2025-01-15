import discord
import asyncio
from custom.gear import Item
EMBED_NEWLINE = "\u200b"


class InventoryEmbed(discord.Embed):
    def __init__(self, inventory: list[Item], title="Inventory"):
        super().__init__(title=title)
        self.inventory = inventory
        self.page = 1
        self.initialize_with_blank_fields()
        self.update_items()

    # needed for set_field_at method in update_items to properly function
    # Initialize pattern of 2 inline + 1 separator, repeated 5 times
    def initialize_with_blank_fields(self):
        for i in range(5):  # 5 rows of 2 items each = 10 items total
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=True)
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=True)
            self.add_field(name=EMBED_NEWLINE, value=EMBED_NEWLINE, inline=False)

    # embed update from hell
    def update_items(self):
        slice_start = (self.page - 1) * 10
        max_items = min(len(self.inventory), slice_start + 10)
        working_inv = self.inventory[slice_start:max_items]

        field_index = 0  # Track actual field position including separators
        for i in range(0, len(working_inv), 2):
            # First item
            item = working_inv[i]
            self.set_field_at(field_index,
                              name=f"{item.emoji} {item.name}",
                              value=f"Quantity:{item.quantity}\nWorth: {item.value}g each",
                              inline=True)
            field_index += 1

            # Second item if exists
            if i + 1 < len(working_inv):
                item = working_inv[i + 1]
                self.set_field_at(field_index,
                                  name=f"{item.emoji} {item.name}",
                                  value=f"Quantity:{item.quantity}\nWorth: {item.value}g each",
                                  inline=True)
                field_index += 1
            else:
                # Empty second slot
                self.set_field_at(field_index,
                                  name=EMBED_NEWLINE,
                                  value=EMBED_NEWLINE,
                                  inline=True)
                field_index += 1

            # Separator after pair
            self.set_field_at(field_index,
                              name=EMBED_NEWLINE,
                              value="\n\n\n",
                              inline=False)
            field_index += 1

        # Clear remaining fields
        while field_index < 15:  # 15 total fields (5 rows × 3 fields per row)
            self.set_field_at(field_index,
                              name=EMBED_NEWLINE,
                              value=EMBED_NEWLINE,
                              inline=True if field_index % 3 != 2 else False)
            field_index += 1


class InventorySelect(discord.ui.Select):
    def __init__(self, inventory: list[Item], placeholder="Select Item", max_values=1, row=0):
        super().__init__(placeholder=placeholder, min_values=1, max_values=max_values, row=row)
        self.inventory = inventory
        self.page = 1
        self.update_options()

    def update_options(self):
        max_items = min(len(self.inventory), self.page * 10)
        slice_start = (self.page - 1) * 10
        # Create new options list
        self.options = [
            discord.SelectOption(
                label=item.name,
                emoji=item.emoji,
                value=f"{i}"
            ) for i, item in enumerate(self.inventory[slice_start:max_items], slice_start)
        ]

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = int(self.values[0])
        self.view.interaction = interaction
        self.view.event.set()


class PreviousButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Previous", emoji="⬅️", row=1, disabled=True)

    async def callback(self, interaction):
        await interaction.response.defer()
        self.view.select.page -= 1
        self.view.embed.page -= 1
        await self.view.correct_inventory_response()


class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Next", emoji="➡️", row=1)

    async def callback(self, interaction):
        await interaction.response.defer()
        self.view.select.page += 1
        self.view.embed.page += 1
        await self.view.correct_inventory_response()


class InventoryView(discord.ui.View):
    def __init__(self, interaction, inventory: list[Item], embed):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.select = InventorySelect(inventory)
        self.embed: InventoryEmbed = embed
        self.event = asyncio.Event()
        self.back_button = PreviousButton()
        self.next_button = NextButton()
        self.add_item(self.back_button)
        self.add_item(self.next_button)
        self.add_item(self.select)
        self.choice = None
        self.correct_buttons()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red, row=4)
    async def back_button(self, interaction: discord.Interaction, button):
        self.choice = -1
        self.interaction = interaction
        self.event.set()

    async def correct_inventory_response(self):
        self.correct_buttons()
        self.correct_select()
        self.correct_embed()
        await self.interaction.edit_original_response(view=self, embed=self.embed)

    def correct_buttons(self):
        self.back_button.disabled = self.select.page <= 1

        total_pages = (len(self.select.inventory) + 9) // 10
        self.next_button.disabled = self.select.page >= total_pages

    def correct_select(self):
        self.select.update_options()

    def correct_embed(self):
        self.embed.update_items()

    async def wait(self):
        await self.event.wait()


