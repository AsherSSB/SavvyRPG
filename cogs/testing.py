import discord
from discord.ext import commands
import asyncio 
import custom.stattable as sts
from custom.playable_character import PlayableCharacter
import random
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Item():
    name: str
    value: int = field(default=0, kw_only=True)
    stack_size: int = field(default=1, kw_only=True)
    quantity: int = field(default=1, kw_only=True)


@dataclass
class PlayerPracticalStats():
    dodge: float
    resistance: float
    

@dataclass
class WeaponStatTable():
    dmg: int
    spd: float
    rng: int
    cc: float
    cm: float
    acc: float
    scalar: float
    stat: str


@dataclass
class Entity():
    name: str
    hp: int
    position: list[int]
    emoji: str

# currently used by both players and enemies, should maybe change that later
class Cooldown():
    def __init__(self, name, emoji, stats: WeaponStatTable, active, acted):
        self.name: str = name
        self.emoji: str = emoji
        self.stats: WeaponStatTable = stats
        self.active: Callable = active
        self.acted: str = acted

    def in_range(self, mypos, targetpos) -> bool:
        if abs(targetpos - mypos) <= self.stats.rng:
            return True
        return False

    def miss(self) -> bool:
        if random.random() < self.stats.acc:
            return False
        return True

    def calculate_crit(self) -> int:
        if random.random() < self.stats.cc:
            return self.stats.cm
        return 1.0
    
    def scale_damage(self, player:PlayableCharacter):
        playerstats = player.stats.to_dict()
        playerstats = playerstats[self.stats.stat]
        if playerstats > 10:
            self.stats.dmg = int(self.stats.dmg * self.stats.scalar * playerstats)

@dataclass
class Weapon(Item):
    cooldown: Cooldown
    scale: str
    slots: int = field(default=2, kw_only=True)


@dataclass
class Drops():
    xp: int
    gold: int
    item: Item | None


@dataclass
class NPCStatTable():
    hp: int
    resist: float
    speed: int


class EnemyCooldown(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)

    def attack(self, entities: list[Entity], playerindex: int) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        entities[playerindex].hp -= dmg
        return f"{hit} {entities[playerindex].name} for {dmg} damage"


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, attack:EnemyCooldown, emoji: str):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.attack = attack
        self.emoji = emoji


class SingleTargetAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)

    def attack(self, enemy:Entity) -> str:
        if self.miss():
            return f"missed {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        enemy.hp -= dmg
        return f"{hit} {enemy.name} for {dmg} damage"

BASE_TILE = ":green_square:"


class CombatInstance():
    def __init__(self, interaction:discord.Interaction, players:list[PlayableCharacter], cooldowns:list[list[Cooldown]], enemies:list[Enemy]):
        self.interaction = interaction
        self.bounds = (6, 4)
        self.game_grid = self.initialize_game_bounds(self.bounds[1], self.bounds[0])
        self.enemies:list[Enemy] = enemies
        self.players: list[PlayableCharacter] = players
        self.cooldowns: list[list[Cooldown]] = cooldowns
        self.entities: list[Entity] = self.initialize_entities()
        self.scale_cooldown_damages(self.cooldowns, self.players)
        self.embed_handler = CombatEmbedHandler(self.entities, self.interaction, self.game_grid)
        self.view = self.initialize_combat_view()
        self.initialize_enemy_cooldowns()


    async def combat(self):
        choice = 0
        await self.interaction.response.send_message("Combat", view=self.view, embed=self.embed_handler.embed)
        # general combat loop
        while True:
            
            # player turn loop
            await self.view.wait()
            choice = self.view.choice
            while choice != -2:

                if choice == -1:
                    if self.try_run():
                        return 0
                    else:
                        await self.embed_handler.log(self.entities[0].name, "Failed to Run")
                else:
                    confirmed = await self.use_cooldown(self.cooldowns[0][choice], 0)
                    if confirmed == True:
                        await self.view.disable_cooldowns(True)

                # enemy is dead
                if self.entities[-1].hp <= 0:
                    return 1
                
                self.view.event = asyncio.Event()
                await self.view.wait()
                choice = self.view.choice
                
            await self.interaction.edit_original_response(view=None)
            await self.embed_handler.log(self.entities[0].name, "Ended their turn")
            
            await self.enemy_attack(-1)
            # player is dead
            if self.entities[0].hp <=0:
                return -1
            # take away player view
            # reset view event
            await self.view.reset()

    def stringify_game_grid(self):
        return '\n'.join(''.join(row) for row in self.bounds)

    def initialize_game_bounds(self, rows, columns):
        return [[BASE_TILE for _ in range(columns)] for _ in range(rows)]

    def initialize_enemy_cooldowns(self):
        cds = []
        for enemy in self.enemies:
            cds.append(enemy.attack)
        self.cooldowns.append(cds)

    def initialize_entities(self) -> list[Entity]:
        entities: list[Entity] = []
        origin_emojis = {
            "Barbarian" : ":axe:" 
        }
        for i, player in enumerate(self.players):
            emoji = origin_emojis[str(player.origin)]
            entities.append(Entity(player.name, self.calculate_player_hp(player), [0, i], emoji))
            self.game_grid[i][0] = emoji
        for i, enemy in enumerate(self.enemies):
            entities.append(Entity(enemy.name, enemy.stats.hp, [self.bounds[0]-1, i], enemy.emoji))
            self.game_grid[i][self.bounds[0]-1] = enemy.emoji
        return entities



    async def append_user_not_in_range(self, playerindex):
        await self.embed_handler.log(f"{self.players[playerindex].name}", "Out of Range!")

    def scale_cooldown_damages(self, all_players_cooldowns: list[list[Cooldown]], players: list[PlayableCharacter]):
        for i, player in enumerate(players):
            for cooldown in all_players_cooldowns[i]:
                cooldown.scale_damage(player)

    async def use_cooldown(self, cooldown:Cooldown, playerindex):
        view = EnemySelectView() 
        view.add_item(EnemySelectMenu([enemy.name for enemy in self.enemies]))
        await self.interaction.edit_original_response(view=view)
        await view.wait()

        if not self.enemy_in_range(self.entities[-view.choice], self.entities[0], cooldown.stats.rng):
            await self.embed_handler.log(self.players[playerindex].name, "Enemy not in range!")
            return await self.use_cooldown(cooldown, playerindex)
        
        await self.interaction.edit_original_response(view=self.view)
        if view.choice == 0:
            return False
        else:
            await self.embed_handler.log(self.players[playerindex].name, cooldown.attack(self.entities[-1]))
            return True

    # currently initializes all cooldowns on row 1
    # errors out if the user has > 5 cooldowns
    def initialize_combat_view(self):
        view = CombatView(self.interaction, self.embed_handler, self.entities, self.bounds, 2, self.game_grid, 0, len(self.players))
        for i, cd in enumerate(self.cooldowns[0]):
            button = CooldownButton(cd.name, i, cd.stats.rng, cd.emoji, row=0)
            view.cooldown_buttons.append(button)
            view.add_item(button)
        view.enable_moves_if_in_range_disable_if_not()
        return view

    async def enemy_attack(self, enemy_index: int):
        entities = self.entities
        cd: EnemyCooldown = self.cooldowns[-1][-1]

        if not self.enemy_in_range(entities[enemy_index], entities[0], cd.stats.rng):
            self.move_toward_player(entities, enemy_index, 0)
            await self.embed_handler.fix_embed_players()

        if self.enemy_in_range(entities[enemy_index], entities[0], cd.stats.rng):
            message = cd.attack(entities, 0)
            await self.embed_handler.log(entities[enemy_index].name, message)
        
    def enemy_in_range(self, enemy, player, max_range):
        horizontal_distance = abs(enemy.position[0] - player.position[0])
        vertical_distance = abs(enemy.position[1] - player.position[1])
        # Check if both distances are within the maximum range
        return horizontal_distance <= max_range and vertical_distance <= max_range

    def move_toward_player(self, entities, enemy_index, player_index):
        enemy = entities[enemy_index]
        player = entities[player_index]
        diff = [p - e for p, e in zip(player.position, enemy.position)]
        
        # Store potential new position
        new_pos = enemy.position.copy()
        
        # Try horizontal movement if player is further horizontally
        if abs(diff[0]) > abs(diff[1]):
            # Try moving left/right
            new_pos[0] += -1 if diff[0] < 0 else 1
            if (0 <= new_pos[0] < len(self.game_grid[0]) and 
                self.game_grid[enemy.position[1]][new_pos[0]] == BASE_TILE):
                # Valid horizontal move
                    self.game_grid[enemy.position[1]][enemy.position[0]] = BASE_TILE
                    enemy.position[0] = new_pos[0]
                    self.game_grid[enemy.position[1]][enemy.position[0]] = enemy.emoji
                    return
                
        # Try vertical movement
        new_pos = enemy.position.copy() 
        new_pos[1] += -1 if diff[1] < 0 else 1
        if (0 <= new_pos[1] < len(self.game_grid) and
            self.game_grid[new_pos[1]][enemy.position[0]] == BASE_TILE):
                # Valid vertical move
                self.game_grid[enemy.position[1]][enemy.position[0]] = BASE_TILE
                enemy.position[1] = new_pos[1]
                self.game_grid[enemy.position[1]][enemy.position[0]] = enemy.emoji

    # always uses player 0 because run only works in single player
    def try_run(self):
        prob = self.calculate_run_probability(self.players[0])
        return random.random() < prob
    
    def calculate_run_probability(self, player: PlayableCharacter):
        # advantage = self.players[playerindex] - self.enemy.stats.speed
        # return 0.5 + 0.05 * advantage
        return 0.5
    
    def calculate_player_hp(self, player:PlayableCharacter):
        return int((10 + (player.level * 2)) * (player.stats.wil * .1))


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

    # this breaks with more than 2 players because of static insert location
    async def log(self, name: str, message: str):
        self.embed = self.embed.insert_field_at(-3, name=name, value=message, inline=False)
        self.logcount += 1
        self.trim()
        await self.fix_embed_players()

    def trim(self):
        if self.logcount > 10:
            self.embed = self.embed.remove_field(0)

    async def fix_embed_players(self):
        for i in range(1, len(self.entities) + 1):
            entity = self.entities[-i]
            self.embed.set_field_at(-i, name=entity.name, value=f"hp: {entity.hp}")
        self.embed.set_field_at(-i-1, value=self.stringify_game_grid(), name="Game Board", inline=False)
        await self.interaction.edit_original_response(embed=self.embed)

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
        super().__init__(placeholder=f"Select Target", min_values=min_values, 
                         max_values=max_values, options=options, row=0)

    def initialize_options(self, enemies: list[str]):
        return [EnemySelectOption(enemy, i) for i, enemy in enumerate(enemies, 1)]

    async def callback(self, interaction: discord.Interaction):
        selected_option = int(self.values[0])  # Convert the selected value back to integer
        self.view.choice = selected_option
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


class CombatView(discord.ui.View):
    def __init__(self, interaction:discord.Interaction, embed_handler, entities, bounds, moves, board, playerid, playercount):
        super().__init__()
        self.player = entities[playerid]
        self.playercount = playercount
        self.entities= entities
        self.embed_handler = embed_handler
        self.event = asyncio.Event()
        self.choice:int
        self.interaction = interaction
        self.add_item(RunButton())
        self.base_moves = moves
        self.moves = moves
        self.initialize_movement_buttons(bounds, board)
        self.cooldown_buttons: list[CooldownButton] = []
        self.cooldown_used: bool = False

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
            if button.row == 0:
                button.disabled = status
        await self.interaction.edit_original_response(view=self)

    async def reset(self):
        self.moves = self.base_moves
        self.forward_button.disabled = False
        self.back_button.disabled = False
        self.up_button.disabled = False
        self.down_button.disabled = False
        self.cooldown_used = False
        await self.disable_cooldowns(False)
        self.event = asyncio.Event()
        self.enable_moves_if_in_range_disable_if_not()
        await self.interaction.edit_original_response(view=self)

    async def disable_moves_if_zero(self):
        if self.moves <= 0:
            self.forward_button.disabled = True
            self.back_button.disabled = True
            self.up_button.disabled = True
            self.down_button.disabled = True
            await self.interaction.edit_original_response(view=self)

    async def adjust_buttons(self):
        changes_made = self.enable_moves_if_in_range_disable_if_not()

        if changes_made:
            await self.interaction.edit_original_response(view=self)
    
    def enable_moves_if_in_range_disable_if_not(self):
        changes_made = False
        enemies = self.entities[self.playercount:]

        for button in filter(lambda x: x.disabled, self.cooldown_buttons):
            if any(self.enemy_in_range(enemy, self.player, button.rng) for enemy in enemies):
                button.disabled = False
                changes_made = True

        for button in filter(lambda x: not x.disabled, self.cooldown_buttons):
            if all(not self.enemy_in_range(enemy, self.player, button.rng) for enemy in enemies):
                button.disabled = True
                changes_made = True

        return changes_made

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
        await interaction.response.defer() # ▶ ◀


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
            await self.view.embed_handler.fix_embed_players()
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
            await self.view.embed_handler.fix_embed_players()
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
            await self.view.embed_handler.fix_embed_players()
        await interaction.response.defer()


class TestingView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.event = asyncio.Event()
        self.interaction:discord.Interaction

    @discord.ui.button(label="Begin Combat Test", style=discord.ButtonStyle.green)
    async def test_button(self, interaction:discord.Interaction, button):
        self.interaction = interaction
        self.event.set()

    async def wait(self):
        await self.event.wait()

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.punchcd = SingleTargetAttack("Punch", "👊", WeaponStatTable(
            dmg=10, spd=3.5, rng=2, cc=0.2, cm=1.5, acc=.9, scalar=.1, stat="str"
        ), acted="punched")

        self.pummelcd = SingleTargetAttack("Pummel", "✊", WeaponStatTable(
            dmg=30, spd=7.5, rng=1, cc=0.2, cm=1.5, acc=0.9, scalar=0.1, stat="str" 
        ), acted="pummeled")    

    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):

        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        enemy:Enemy = Enemy("Training Dummy", 
                    NPCStatTable(120, 0, 0), 
                    Drops(1, 1, None),
                    EnemyCooldown("Smack", None, WeaponStatTable(
            dmg=1, spd=7.5, rng=1, cc=0.2, cm=2.0, acc=0.9, scalar=0.1, stat="str" 
        ), "smaccd"), ":dizzy_face:")

        interaction = await self.send_testing_view(interaction)
        instance = CombatInstance(interaction, [self.pc], [[self.punchcd, self.pummelcd]], [enemy])
        result = await instance.combat()
        if result == -1:
            await interaction.edit_original_response(content="You Died.", view=None)
        elif result == 0:
            await interaction.edit_original_response(content="You Successfully Ran.", view=None)
        else:
            await interaction.edit_original_response(content=f"You Defeated {enemy.name}!", view=None)

        await asyncio.sleep(8.0)
        await interaction.delete_original_response()

    async def send_testing_view(self, interaction:discord.Interaction):
        view = TestingView()
        await interaction.response.send_message("""## Combat Test
This test is for demonstration purposes only and is not representative of any finished product.
                                                
**Rules**: 
You may move twice and attack once each turn
You are allowed to try and run once before the option to run is disabled
You must be in range to attack the enemy, Punch has a range of 2, Pummel has a range of 1
The enemy will move to get in range, and then will attack if in range before ending their turn
""", view=view)
        
        await view.wait()
        await interaction.delete_original_response()
        return view.interaction
    

async def setup(bot):
    await bot.add_cog(Testing(bot))