import discord
from discord.ext import commands
import asyncio
import custom.stattable as sts
from custom.playable_character import PlayableCharacter
import random
from custom.stattable import StatTable
from custom.gear import Gear, Loadout
from custom.combat.enemy import Enemy
from custom.combat.view import CombatView, CombatEmbedHandler, CooldownButton, EnemySelectView, EnemySelectMenu, AttackButton
from custom.combat.entities import Entity, NPCStatTable, Drops, EntitiesInfo, PlayerPracticalStats
from custom.combat.cooldown_base_classes import Cooldown, EnemyCooldown, WeaponStatTable, AOEAttack
from custom.combat.barbarian.cooldowns import Execute, Cleave
from items.weapons import Fists, Greatsword
from custom.combat.enemies import TrainingDummy, Wolf, Bandit, Skeleton, DarkMage, Golem

BASE_TILE = ":green_square:"


class CombatInstance():
    def __init__(self, interaction:discord.Interaction, players:list[PlayableCharacter],
                 loadouts:list[Loadout], cooldowns:list[list[Cooldown]], enemies:list[Enemy]):
        self.interaction = interaction
        self.bounds = (6, 4)
        self.game_grid = self.initialize_game_bounds(self.bounds[1], self.bounds[0])
        self.enemies:list[Enemy] = enemies
        self.players: list[PlayableCharacter] = players
        self.loadouts = loadouts
        calculator = PracticalStatsCalculator()
        self.player_practicals: list[PlayerPracticalStats] = calculator.initialize_practical_stats(players, loadouts)
        self.entities: list[Entity] = self.initialize_entities()
        self.cooldowns: list[list[Cooldown]] = cooldowns
        self.pass_entities_to_player_cooldowns()
        self.scale_cooldown_damages(self.cooldowns, self.players)
        self.scale_all_cooldowns_with_practicals()
        self.initialize_enemy_cooldowns()
        self.embed_handler = CombatEmbedHandler(self.entities, self.interaction, self.game_grid)
        # this only works for singleplayer
        self.view = self.initialize_combat_view(loadouts[0])

    async def combat(self):
        choice = 0
        enemies_alive = list(range(-1, -len(self.enemies) - 1, -1))
        await self.view.enable_moves_if_in_range_disable_if_not()
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
                elif choice == 9:
                    confirmed = await self.use_cooldown(self.loadouts[0].weapon[0].cooldown, 0, enemies_alive)
                    if not confirmed:
                        self.view.attacks += 1
                        await self.view.set_attack_button_based_on_attacks_left()
                else:
                    confirmed = await self.use_cooldown(self.cooldowns[0][choice], 0, enemies_alive)
                    if confirmed:
                        await self.view.disable_cooldowns(True)

                # all enemies are dead
                if all(enemy.hp <= 0 for enemy in self.entities[len(self.players):]):
                    return 1

                self.view.event = asyncio.Event()
                await self.view.wait()
                choice = self.view.choice

            await self.interaction.edit_original_response(view=None)
            await self.embed_handler.log(self.entities[0].name, "Ended their turn")

            for enemy_index in enemies_alive:
                if self.entities[enemy_index].hp <= 0:
                    enemies_alive.remove(enemy_index)

            for i in enemies_alive:
                await self.enemy_attack(i)
            # player is dead
            if self.entities[0].hp <= 0:
                return -1
            # take away player view
            # reset view event
            await self.view.reset()

    def scale_all_cooldowns_with_practicals(self):
        for i, practicals in enumerate(self.player_practicals):
            self.scale_cooldown_set_with_practicals(self.cooldowns[i], practicals)

    def scale_cooldown_set_with_practicals(self, cds: list[Cooldown], practicals: PlayerPracticalStats):
        for cd in cds:
            cd.stats.cc = round(cd.stats.cc + practicals.critchance, 2)
            cd.stats.cm = round(cd.stats.cm + practicals.critmult, 2)

    def pass_entities_to_player_cooldowns(self):
        for i, cdlist in enumerate(self.cooldowns):
            entities = EntitiesInfo(self.entities, i, len(self.players), len(self.enemies))
            for j, cd in enumerate(cdlist):
                self.cooldowns[i][j] = cd(entities=entities)
            self.loadouts[i].weapon[0].cooldown.entities = entities

    def stringify_game_grid(self):
        return '\n'.join(''.join(str(row)) for row in self.bounds)

    def initialize_game_bounds(self, rows, columns):
        return [[BASE_TILE for _ in range(columns)] for _ in range(rows)]

    def initialize_enemy_cooldowns(self):
        cds = []
        for i, enemy in enumerate(self.enemies):
            entities = EntitiesInfo(self.entities, i, len(self.players), len(self.enemies))
            enemy.attack.entities = entities
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
                cooldown.scale_damage(player=player)
            self.loadouts[i].weapon[0].cooldown.scale_damage(player=player)

    async def use_cooldown(self, cooldown:Cooldown, playerindex, alive_enemies: list[int]):
        view = EnemySelectView()

        enemies = []
        for i in alive_enemies:
            if self.enemy_in_range(self.entities[i], self.entities[playerindex], cooldown.stats.rng):
                enemies.append((i, self.entities[i].name))

        if isinstance(cooldown, AOEAttack):
            maxselect = len(enemies)
        else:
            maxselect = 1

        view.add_item(EnemySelectMenu(enemies=enemies, max_values=maxselect))
        await self.interaction.edit_original_response(view=view)
        await view.wait()

        await self.interaction.edit_original_response(view=self.view)
        if view.choice == 0:
            return False
        else:
            await self.embed_handler.log(self.players[playerindex].name, cooldown.attack(view.choice))
            return True

    # currently initializes all cooldowns on row 0
    # errors out if the user has > 5 cooldowns,
    # attacks are also being placed on row 0
    def initialize_combat_view(self, loadout: Loadout):
        view = CombatView(self.interaction, self.embed_handler, self.entities, self.bounds, self.player_practicals[0].moves, self.game_grid, 0, len(self.players), self.player_practicals[0].attacks)
        button = AttackButton(name=loadout.weapon[0].name, emoji=loadout.weapon[0].emoji, rng=loadout.weapon[0].cooldown.stats.rng)
        view.attack_button = button
        view.add_item(button)
        for i, cd in enumerate(self.cooldowns[0]):
            button = CooldownButton(cd.name, i, cd.stats.rng, cd.emoji, row=0)
            view.cooldown_buttons.append(button)
            view.add_item(button)
        return view

    # TODO: for some reason enemies still move even if they are in range??
    async def enemy_attack(self, enemy_index: int):
        entities = self.entities
        cd: EnemyCooldown = self.cooldowns[-1][enemy_index]

        moves = self.enemies[enemy_index].stats.moves
        in_range = any(self.enemy_in_range(entities[enemy_index], player, cd.stats.rng) for player in entities[:len(self.players)])
        # INDEX of the closest player in self.entities relative to enemy attacking
        while moves > 0 and not in_range:
            closest_player = self.get_closest_target(entities[enemy_index], entities[:len(self.players)])
            self.move_toward_player(entities, enemy_index, closest_player)
            await self.embed_handler.fix_embed_players()
            await self.interaction.edit_original_response(embed=self.embed_handler.embed)
            moves -= 1

        in_range = any(self.enemy_in_range(entities[enemy_index], player, cd.stats.rng) for player in entities[:len(self.players)])
        if in_range:
            closest_player = self.get_closest_target(entities[enemy_index], entities[:len(self.players)])
            message = cd.attack(closest_player)
            await self.embed_handler.log(entities[enemy_index].name, message)

    def get_closest_target(self, enemy: Entity, players: list[Entity]):
        closest: int
        distance = 1000
        for i, player in enumerate(players):
            horizontal_distance = abs(enemy.position[0] - player.position[0])
            vertical_distance = abs(enemy.position[1] - player.position[1])
            if horizontal_distance + vertical_distance < distance:
                distance = horizontal_distance + vertical_distance
                closest = i

        # returns the INDEX of the closest player in self.entities
        return closest

    def enemy_in_range(self, enemy, player, max_range):
        horizontal_distance = abs(enemy.position[0] - player.position[0])
        vertical_distance = abs(enemy.position[1] - player.position[1])
        # Check if both distances are within the maximum range
        return horizontal_distance <= max_range and vertical_distance <= max_range

    # ALWAYS moves toward the closest player in proximity
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
            return

        new_pos = enemy.position.copy()
        new_pos[0] += -1 if diff[0] < 0 else 1
        if (0 <= new_pos[0] < len(self.game_grid[0]) and
            self.game_grid[enemy.position[1]][new_pos[0]] == BASE_TILE):
            # Valid horizontal move
            self.game_grid[enemy.position[1]][enemy.position[0]] = BASE_TILE
            enemy.position[0] = new_pos[0]
            self.game_grid[enemy.position[1]][enemy.position[0]] = enemy.emoji
            return

        new_pos = enemy.position.copy()
        new_pos[1] += 1
        if (0 <= new_pos[1] < len(self.game_grid) and
            self.game_grid[new_pos[1]][enemy.position[0]] == BASE_TILE):
            # Valid vertical move
            self.game_grid[enemy.position[1]][enemy.position[0]] = BASE_TILE
            enemy.position[1] = new_pos[1]
            self.game_grid[enemy.position[1]][enemy.position[0]] = enemy.emoji
            return

    # always uses player 0 because run only works in single player
    def try_run(self):
        prob = self.calculate_run_probability(self.players[0])
        return random.random() < prob

    def calculate_run_probability(self, alive_enemies: list[Enemy]):
        fastest = max([enemy.stats.moves for enemy in alive_enemies])
        player_speed = self.player_practicals[0].moves
        diff = player_speed - fastest
        return 0.5 + diff * .15

    def calculate_player_hp(self, player:PlayableCharacter):
        return int((10 + (player.level * 2)) * (player.stats.wil * .1))


class PracticalStatsCalculator():
    def __init__(self):
        self.gear_slots = ['head', 'chest', 'hands', 'legs', 'feet']

    def initialize_practical_stats(self, players: list[PlayableCharacter], loadouts: list[Loadout]):
        practicals = []
        # initialize gear base stats
        for loadout in loadouts:
            practicals.append(self.calculate_practical_stats(loadout))
        # initialize gear special stats
        for i, practical in enumerate(practicals):
            self.populate_special_stats(players[i], loadouts[i], practical)
        return practicals

    def populate_special_stats(self, player: PlayableCharacter, loadout: Loadout, practical: PlayerPracticalStats):
        practical.moves = self.calculate_moves(player, loadout)
        practical.attacks = self.calculate_attacks(loadout)
        practical.healing = self.calculate_healing(loadout)
        practical.multicast = self.calculate_multicast(loadout)
        practical.critchance = self.calculate_critchance(player, loadout)
        practical.critmult = self.calculate_critmult(player, loadout)

    def calculate_moves(self, player: PlayableCharacter, loadout:Loadout):
        moves = 3
        moves += player.stats.att // 5 - 2
        if loadout.feet is not None:
            moves += loadout.feet.moves
        return moves

    def calculate_attacks(self, loadout: Loadout):
        attacks = 1
        if loadout.chest is not None:
            attacks += loadout.chest.attacks
        if loadout.hands is not None:
            attacks += loadout.hands.attacks
        return attacks

    def calculate_healing(self, loadout: Loadout):
        healing = 0.0
        if loadout.chest is not None:
            healing = round(healing + loadout.chest.healing, 2)
        if loadout.legs is not None:
            healing = round(healing + loadout.legs.healing, 2)
        return healing

    def calculate_multicast(self, loadout: Loadout):
        multicast = 0.0
        if loadout.head is not None:
            multicast = round(multicast + loadout.multicast, 2)
        return multicast

    def calculate_critchance(self, player: PlayableCharacter, loadout: Loadout):
        critchance = 0.0
        player_crit = player.stats.dex * 0.05 - 0.5
        critchance = round(critchance + player_crit, 2)
        if loadout.feet is not None:
            critchance = round(critchance + loadout.feet.critchance, 2)
        if loadout.head is not None:
            critchance = round(critchance + loadout.head.critchance, 2)
        return critchance

    def calculate_critmult(self, player: PlayableCharacter, loadout: Loadout):
        critmult = 1.0
        player_crit = player.stats.att * 0.1 - 1.0
        critmult = round(critmult + player_crit, 2)
        if loadout.hands is not None:
            critmult = round(critmult + loadout.hands.critmult, 2)
        if loadout.legs is not None:
            critmult = round(critmult + loadout.legs.critmult, 2)
        return critmult

    def calculate_practical_stats(self, loadout: Loadout):
        # calculate total resistance given gear
        resistances = []
        dodges = []

        for slot in self.gear_slots:
            gear = getattr(loadout, slot)
            if gear is not None:
                resistances.append(gear.stats.resist)
                dodges.append(gear.stats.dodge)
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
        return PlayerPracticalStats(dodge=hitchance, resistance=resistmult)


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

    @discord.app_commands.command(name="combat")
    async def test_combat(self, interaction:discord.Interaction):
        self.pc:PlayableCharacter = PlayableCharacter(
            "Player", "test", sts.Human(), sts.Barbarian(), xp=0, gold=0)

        testwep = Greatsword()
        enemy = Wolf()
        enemy2 = TrainingDummy()
        enemy3 = TrainingDummy()

        loadout = Loadout(None, None, None, None, None, [testwep])

        interaction = await self.send_testing_view(interaction)
        instance = CombatInstance(interaction, [self.pc], [loadout],[[Cleave, Execute]], [enemy2, enemy3, enemy])
        result = await instance.combat()
        if result == -1:
            await interaction.edit_original_response(content="You Died.", view=None)
        elif result == 0:
            await interaction.edit_original_response(content="You Successfully Ran.", view=None)
        else:
            await interaction.edit_original_response(content=f"You Defeated {enemy.name}!", view=None)

        await asyncio.sleep(4.0)
        await interaction.edit_original_response(content=f"Rewards\nGold: {enemy.drops.gold}\nXP: {enemy.drops.xp}", embed=None)
        await asyncio.sleep(4.0)
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

