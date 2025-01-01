import discord
from discord.ext import commands
import asyncio
import custom.stattable as sts
from custom.playable_character import PlayableCharacter
import random
from custom.gear import Gear, Loadout
from custom.combat.enemy import Enemy
from custom.combat.view import CombatView, CombatEmbedHandler, CooldownButton, EnemySelectView, EnemySelectMenu
from custom.combat.entities import Entity, NPCStatTable, Drops, EntitiesInfo, PlayerPracticalStats
from custom.combat.cooldown_base_classes import Cooldown, SingleTargetAttack, EnemyCooldown, WeaponStatTable

BASE_TILE = ":green_square:"


class CombatInstance():
    def __init__(self, interaction:discord.Interaction, players:list[PlayableCharacter],
                 loadouts:list[Loadout], cooldowns:list[list[Cooldown]], enemies:list[Enemy]):
        self.interaction = interaction
        self.bounds = (6, 4)
        self.game_grid = self.initialize_game_bounds(self.bounds[1], self.bounds[0])
        self.enemies:list[Enemy] = enemies
        self.players: list[PlayableCharacter] = players
        self.player_practicals: list[PlayerPracticalStats] = self.initialize_practical_stats(loadouts)
        self.entities: list[Entity] = self.initialize_entities()
        self.cooldowns: list[list[Cooldown]] = cooldowns
        self.scale_cooldown_damages(self.cooldowns, self.players)
        self.embed_handler = CombatEmbedHandler(self.entities, self.interaction, self.game_grid)
        self.view = self.initialize_combat_view()
        # cooldowns need EntitiesInfo
        self.initialize_enemy_cooldowns()
        self.pass_entities_to_cooldowns()

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
                    if confirmed:
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
            if self.entities[0].hp <= 0:
                return -1
            # take away player view
            # reset view event
            await self.view.reset()

    def pass_entities_to_cooldowns(self):
        for i, cdlist in enumerate(self.cooldowns):
            entities = EntitiesInfo(self.entities, i, len(self.players), len(self.enemies))
            for cd in cdlist:
                cd.entities = entities

    def initialize_practical_stats(self, gear: list[Loadout]):
        practicals = []
        for loadout in gear:
            practicals.append(self.calculate_practical_stats(loadout))
        return practicals

    def calculate_practical_stats(self, loadout: Loadout):
        # calculate total resistance given gear
        resistances = []
        dodges = []
        for value in vars(loadout).values():
            if value is not None:
                resistances.append(value.stats.resist)
                dodges.append(value.stats.dodge)
            else:
                resistances.append(0.0)
                dodges.append(0.0)

        # Calculate combined resistance
        total = 1.0
        for r in resistances:
            total *= (1 - r)

        # Apply scaling factor to approach but never reach 95%
        # resistmult is the MULTIPLIER applied to damage
        # smaller resistmult = higher resistance
        resistmult = round(1 - (1 - total) * 0.95, 2)

        total = 1.0
        for d in dodges:
            total *= (1 - d)

        hitchance = round(1 - (1 - total) * 0.85, 2)
        return PlayerPracticalStats(hitchance, resistmult)

    def stringify_game_grid(self):
        return '\n'.join(''.join(str(row)) for row in self.bounds)

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
            "Barbarian": ":axe:"
        }
        for i, player in enumerate(self.players):
            emoji = origin_emojis[str(player.origin)]
            entities.append(Entity(player.name, self.calculate_player_hp(player), self.player_practicals[i].resistance, self.player_practicals[i].dodge, [0, i], emoji))
            self.game_grid[i][0] = emoji
        for i, enemy in enumerate(self.enemies):
            entities.append(Entity(enemy.name, enemy.stats.hp, enemy.stats.resist, enemy.stats.dodge,[self.bounds[0] - 1, i], enemy.emoji))
            self.game_grid[i][self.bounds[0] - 1] = enemy.emoji
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
            message = cd.attack(0)
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


class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.punchcd = SingleTargetAttack("Punch", "👊", WeaponStatTable(
            dmg=10, spd=1, rng=2, cc=0.2, cm=1.5, acc=.9, scalar=.1, stat="str"
        ), acted="punched")

        self.pummelcd = SingleTargetAttack("Pummel", "✊", WeaponStatTable(
            dmg=30, spd=2, rng=1, cc=0.2, cm=1.5, acc=0.9, scalar=0.1, stat="str"
        ), acted="pummeled")

    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):

        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        enemy:Enemy = Enemy("Training Dummy",
                            NPCStatTable(120, 1.0, 1.0),
                            Drops(1, 1, None),
                            EnemyCooldown("Smack", None,
                                          WeaponStatTable(
                                              dmg=1, spd=3, rng=1, cc=0.2, cm=2.0, acc=0.9, scalar=0.1, stat="str"),
                                          "smaccd"), ":dizzy_face:")

        loadout = Loadout(None, None, None, None, None)

        interaction = await self.send_testing_view(interaction)
        instance = CombatInstance(interaction, [self.pc], [loadout],[[self.punchcd, self.pummelcd]], [enemy])
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
    await bot.add_cog(Combat(bot))

