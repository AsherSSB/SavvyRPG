import discord
import asyncio
from custom.combat.entities import Entity

BASE_TILE = ":green_square:"


class CombatEmbed(discord.Embed):
    def __init__(self):
        super().__init__(color=None, title="Combat", description=None)


class CombatEmbedHandler():
    def __init__(self, entities: list[Entity], interaction:discord.Interaction, game_board: list[list[str]]):
        self.embed = CombatEmbed()
        self.logcount = 0
        self.entities = entities
        self.interaction = interaction
        self.game_board = game_board
        self.embed.add_field(value=self.stringify_game_grid(), name="Game Board", inline=False)
        for entity in entities:
            self.embed.add_field(name=entity.name, value=f"hp: {entity.hp}", inline=True)

    # this breaks with more than 2 entities because of static insert location
    async def log(self, name: str, message: str):
        # + 2 for the board and for negetive indexing being one based
        self.embed = self.embed.insert_field_at(-(len(self.entities) + 1), name=name, value=message, inline=False)
        self.logcount += 1
        self.trim()
        await self.fix_embed_players()
        await self.interaction.edit_original_response(embed=self.embed)

    def trim(self):
        if self.logcount > 10:
            self.embed = self.embed.remove_field(0)

    async def fix_embed_players(self):
        for i in range(1, len(self.entities) + 1):
            entity = self.entities[-i]
            content = f"hp: {entity.hp}"
            for key, value in entity.status.items():
                content += f"\n{key}: {value} turn(s)"
            self.embed.set_field_at(-i, name=entity.name, value=content)
        self.embed.set_field_at(-i - 1, value=self.stringify_game_grid(), name="Game Board", inline=False)

    def stringify_game_grid(self):
        return '\n'.join(''.join(row) for row in self.game_board)


class CooldownButton(discord.ui.Button):
    def __init__(self, label, choiceid, rng, emoji, row):
        super().__init__(style=discord.ButtonStyle.green, label=label, emoji=discord.PartialEmoji(name=emoji), row=row)
        self.disabled = False
        self.choiceid = choiceid
        self.rng = rng

    async def callback(self, interaction):
        self.view.choice = self.choiceid
        self.view.cooldown_used = True
        await interaction.response.defer()
        self.view.event.set()


class EnemySelectOption(discord.SelectOption):
    def __init__(self, label: str, value: int):
        super().__init__(label=label, value=str(value))


class EnemySelectMenu(discord.ui.Select):
    def __init__(self, enemies: list[str], min_values=1, max_values=1):
        self.enemies = enemies
        options = self.initialize_options(enemies)
        super().__init__(placeholder="Select Target", min_values=min_values,
                         max_values=max_values, options=options, row=0)

    def initialize_options(self, enemies: list[tuple[int, str]]):
        return [EnemySelectOption(enemy, i) for i, enemy in enemies]

    async def callback(self, interaction: discord.Interaction):
        self.view.choice = [int(value) for value in self.values]
        await interaction.response.defer()
        self.view.event.set()


class EnemySelectView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.choice: int = 0
        self.event = asyncio.Event()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red, row=1)
    async def back_button(self, interaction:discord.Interaction, button):
        await interaction.response.defer()
        self.event.set()

    async def wait(self):
        await self.event.wait()


class RunButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Run", row=4)

    async def callback(self, interaction):
        self.disabled = True
        await self.view.interaction.edit_original_response(view=self.view)
        self.view.choice = -1
        await interaction.response.defer()
        self.view.event.set()


class AttackButton(discord.ui.Button):
    def __init__(self, name, emoji, rng):
        super().__init__(style=discord.ButtonStyle.green, emoji=discord.PartialEmoji(name=emoji), label=name, row=0)
        self.rng = rng

    async def callback(self, interaction):
        self.view.choice = 9
        self.view.attacks -= 1
        await interaction.response.defer()
        self.view.event.set()


class CombatView(discord.ui.View):
    def __init__(self, interaction:discord.Interaction, embed_handler, entities, bounds, moves, board, playerid, playercount, attacks):
        super().__init__()
        self.base_attacks = attacks
        self.attacks = attacks
        self.player = entities[playerid]
        self.playercount = playercount
        self.entities = entities
        self.embed_handler = embed_handler
        self.event = asyncio.Event()
        self.choice:int
        self.interaction = interaction
        if self.playercount == 1:
            self.add_item(RunButton())
        self.base_moves = moves
        self.moves = moves
        self.initialize_movement_buttons(bounds, board)
        self.cooldown_buttons: list[CooldownButton] = []
        self.cooldown_used: bool = False
        self.attack_button: AttackButton = None

    async def set_attack_button_based_on_attacks_left(self):
        enemies = self.entities[self.playercount:]
        has_enemy_in_range = any(self.enemy_in_range(enemy, self.player, self.attack_button.rng) and enemy.hp > 0 for enemy in enemies)
        # Disable if out of attacks OR no enemies in range
        self.attack_button.disabled = (self.attacks <= 0 or not has_enemy_in_range)

    def initialize_movement_buttons(self, bounds, board):
        self.forward_button = ForwardButton(bounds, self.entities, 0, board)
        self.back_button = BackButton(bounds, self.entities, 0, board)
        self.up_button = UpButton(bounds, self.entities, 0, board)
        self.down_button = DownButton(bounds, self.entities, 0, board)
        self.add_item(self.back_button)
        self.add_item(self.forward_button)
        self.add_item(self.up_button)
        self.add_item(self.down_button)

    @discord.ui.button(label="End Turn", style=discord.ButtonStyle.red, row=4)
    async def end_turn_button(self, interaction:discord.Interaction, button):
        self.choice = -2
        await interaction.response.defer()
        self.event.set()

    async def disable_cooldowns(self, status: bool):
        for button in self.children:
            if button.row == 0 and isinstance(button, CooldownButton):
                button.disabled = status
        await self.interaction.edit_original_response(view=self)

    async def reset(self):
        self.moves = self.base_moves
        self.attacks = self.base_attacks
        await self.set_attack_button_based_on_attacks_left()
        self.forward_button.disabled = False
        self.back_button.disabled = False
        self.up_button.disabled = False
        self.down_button.disabled = False
        self.cooldown_used = False
        await self.disable_cooldowns(False)
        self.event = asyncio.Event()
        await self.enable_moves_if_in_range_disable_if_not()
        await self.interaction.edit_original_response(view=self)

    async def disable_moves_if_zero(self):
        if self.moves <= 0:
            self.forward_button.disabled = True
            self.back_button.disabled = True
            self.up_button.disabled = True
            self.down_button.disabled = True
        else:
            self.forward_button.disabled = False
            self.back_button.disabled = False
            self.up_button.disabled = False
            self.down_button.disabled = False

    async def adjust_buttons(self):
        await self.enable_moves_if_in_range_disable_if_not()

    async def enable_moves_if_in_range_disable_if_not(self):
        enemies = self.entities[self.playercount:]

        for button in filter(lambda x: x.disabled, self.cooldown_buttons):
            if any(self.enemy_in_range(enemy, self.player, button.rng) and enemy.hp > 0 for enemy in enemies):
                button.disabled = False

        for button in filter(lambda x: not x.disabled, self.cooldown_buttons):
            if all(not self.enemy_in_range(enemy, self.player, button.rng) or enemy.hp <= 0 for enemy in enemies):
                button.disabled = True

        # This needs to be here for first turn else basic attack always starts enabled
        if any(self.enemy_in_range(enemy, self.player, self.attack_button.rng) for enemy in enemies):
            await self.set_attack_button_based_on_attacks_left()
        else:
            self.attack_button.disabled = True

    def enemy_in_range(self, enemy, player, max_range):
        horizontal_distance = abs(enemy.position[0] - player.position[0])
        vertical_distance = abs(enemy.position[1] - player.position[1])
        return horizontal_distance <= max_range and vertical_distance <= max_range

    async def wait(self):
        await self.event.wait()


class MovementButton(discord.ui.Button):
    def __init__(self, bounds, entities: list[Entity], entityid, board, emoji):
        self.player = entities[entityid]
        self.bounds = bounds
        self.board: list[list[str]] = board
        super().__init__(style=discord.ButtonStyle.gray, label="", emoji=discord.PartialEmoji(name=emoji), row=2)


class ForwardButton(MovementButton):
    def __init__(self, bounds, entities: list[Entity], entityid, board):
        super().__init__(bounds, entities, entityid, board, emoji="➡️")

    async def callback(self, interaction):
        if self.player.position[0] < self.bounds[0] - 1 and self.board[self.player.position[1]][self.player.position[0] + 1] == BASE_TILE:
            self.view.moves -= 1
            await self.view.disable_moves_if_zero()
            self.board[self.player.position[1]][self.player.position[0] + 1] = self.player.emoji
            self.board[self.player.position[1]][self.player.position[0]] = BASE_TILE
            self.player.position[0] += 1
            if not self.view.cooldown_used:
                await self.view.adjust_buttons()
            await self.view.embed_handler.fix_embed_players()
            await self.view.set_attack_button_based_on_attacks_left()
            await self.view.interaction.edit_original_response(view=self.view, embed=self.view.embed_handler.embed)
        await interaction.response.defer()  # ▶ ◀


class BackButton(MovementButton):
    def __init__(self, bounds, entities: list[Entity], entityid, board):
        super().__init__(bounds, entities, entityid, board, "⬅️")

    async def callback(self, interaction):
        # kill me
        if self.player.position[0] > 0 and self.board[self.player.position[1]][self.player.position[0] - 1] == BASE_TILE:
            self.view.moves -= 1
            await self.view.disable_moves_if_zero()
            self.board[self.player.position[1]][self.player.position[0] - 1] = self.player.emoji
            self.board[self.player.position[1]][self.player.position[0]] = BASE_TILE
            self.player.position[0] -= 1
            if not self.view.cooldown_used:
                await self.view.adjust_buttons()
            await self.view.set_attack_button_based_on_attacks_left()
            await self.view.embed_handler.fix_embed_players()
            await self.view.interaction.edit_original_response(view=self.view, embed=self.view.embed_handler.embed)

        await interaction.response.defer()


class UpButton(MovementButton):
    def __init__(self, bounds, entities: list[Entity], entityid, board):
        super().__init__(bounds, entities, entityid, board, "⬆️")

    async def callback(self, interaction):
        # kill me
        if self.player.position[1] > 0 and self.board[self.player.position[1] - 1][self.player.position[0]] == BASE_TILE:
            self.view.moves -= 1
            await self.view.disable_moves_if_zero()
            self.board[self.player.position[1] - 1][self.player.position[0]] = self.player.emoji
            self.board[self.player.position[1]][self.player.position[0]] = BASE_TILE
            self.player.position[1] -= 1
            if not self.view.cooldown_used:
                await self.view.adjust_buttons()
            await self.view.set_attack_button_based_on_attacks_left()
            await self.view.embed_handler.fix_embed_players()
            await self.view.interaction.edit_original_response(view=self.view, embed=self.view.embed_handler.embed)

        await interaction.response.defer()


class DownButton(MovementButton):
    def __init__(self, bounds, entities: list[Entity], entityid, board):
        super().__init__(bounds, entities, entityid, board, "⬇️")

    async def callback(self, interaction):
        # kill me
        if self.player.position[1] < self.bounds[1] - 1 and self.board[self.player.position[1] + 1][self.player.position[0]] == BASE_TILE:
            self.view.moves -= 1
            await self.view.disable_moves_if_zero()
            self.board[self.player.position[1] + 1][self.player.position[0]] = self.player.emoji
            self.board[self.player.position[1]][self.player.position[0]] = BASE_TILE
            self.player.position[1] += 1
            if not self.view.cooldown_used:
                await self.view.adjust_buttons()
            await self.view.set_attack_button_based_on_attacks_left()
            await self.view.embed_handler.fix_embed_players()
            await self.view.interaction.edit_original_response(view=self.view, embed=self.view.embed_handler.embed)

        await interaction.response.defer()

