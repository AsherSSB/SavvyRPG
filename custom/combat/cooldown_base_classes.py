from typing import Callable
import random
from custom.playable_character import PlayableCharacter
from custom.combat.entities import Entity, EntitiesInfo
from custom.combat.view import CombatView
from dataclasses import dataclass

BASE_TILE = ":green_square:"


@dataclass
class WeaponStatTable():
    dmg: int
    spd: int
    rng: int
    cc: float
    cm: float
    acc: float
    scalar: float
    stat: str


class Cooldown():
    def __init__(self, name, emoji, stats: WeaponStatTable, active, acted, entities):
        self.name: str = name
        self.emoji: str = emoji
        self.stats: WeaponStatTable = stats
        self.active: Callable = active
        self.acted: str = acted
        self.entities: EntitiesInfo = entities

    def in_range(self, mypos, targetpos) -> bool:
        if abs(targetpos - mypos) <= self.stats.rng:
            return True
        return False

    def miss(self) -> bool:
        if random.random() < self.stats.acc:
            return False
        return True

    def calculate_crit(self) -> float:
        if random.random() < self.stats.cc:
            return self.stats.cm
        return 1.0

    def scale_damage(self, player:PlayableCharacter):
        playerstats = player.stats.to_dict()
        playerstats = playerstats[self.stats.stat]
        if playerstats > 10:
            self.stats.dmg = int(self.stats.dmg * (1 + self.stats.scalar * (playerstats - 10)))

    # needs to be defined in child classes
    def attack(self, target_indexes: list[int]):
        pass


class EnemyCooldown(Cooldown):
    def __init__(self, name, stats):
        super().__init__(name=name, emoji="�", stats=stats, active=self.attack, acted="struck", entities=None)

    def attack(self, playerindex: int) -> str:
        if self.miss():
            return f"missed {self.name}"
        if random.random() > self.entities.lst[playerindex].dodge:
            return f"{self.entities.lst[playerindex].name} dodged {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult * self.entities.lst[playerindex].res)
        self.entities.lst[playerindex].hp -= dmg
        return f"{hit} {self.entities.lst[playerindex].name} {self.name} for {dmg} damage"


class SingleTargetAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted, entities):
        super().__init__(name, emoji, stats, self.attack, acted, entities=entities)

    def attack(self, target_indexes: list[int]) -> str:
        enemy = self.entities.lst[target_indexes[0]]
        if self.miss():
            return f"missed {self.name}"
        if random.random() < enemy.dodge:
            return f"{enemy.name} dodged {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult * enemy.res)
        enemy.hp -= dmg
        return f"{hit} {enemy.name} for {dmg} damage"


class AOEAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted, entities):
        super().__init__(name, emoji, stats, self.attack, acted, entities=entities)

    def attack(self, target_indexes: list[int]):
        entities = [self.entities.lst[index] for index in target_indexes]
        message = self.name
        for entity in entities:
            if self.miss():
                message += f" missed {entity.name},"
                continue
            if random.random() < entity.dodge:
                message += f" was dodged by {entity.name},"
                continue
            mult = self.calculate_crit()
            dmg = int(self.stats.dmg * mult * entity.res)
            entity.hp -= dmg
            message += f" hit {entity.name} for {dmg},"
        # remove trailing comma
        message = message[0:-1]
        return message


class MovingSingleTargetAttack(SingleTargetAttack):
    def __init__(self, name, emoji, stats, acted, entities, game_grid=None):
        self.game_grid = game_grid
        super().__init__(name=name, emoji=emoji, stats=stats, acted=acted, entities=entities)

    def in_range(self, enemy, player, max_range):
        horizontal_distance = abs(enemy.position[0] - player.position[0])
        vertical_distance = abs(enemy.position[1] - player.position[1])
        # Check if both distances are within the maximum range
        return horizontal_distance <= max_range and vertical_distance <= max_range

    def move_toward_enemy(self, enemy_i):
        player = self.entities.lst[self.entities.user_index]
        enemy = self.entities.lst[enemy_i]
        diff = [p - e for p, e in zip(enemy.position, player.position)]

        # Store potential new position
        new_pos = player.position.copy()

        # Try horizontal movement if enemy is further horizontally
        if abs(diff[0]) > abs(diff[1]):
            # Try moving left/right
            new_pos[0] += -1 if diff[0] < 0 else 1
            if (0 <= new_pos[0] < len(self.game_grid[0]) and
                self.game_grid[player.position[1]][new_pos[0]] == BASE_TILE):
                # Valid horizontal move
                self.game_grid[player.position[1]][player.position[0]] = BASE_TILE
                player.position[0] = new_pos[0]
                self.game_grid[player.position[1]][player.position[0]] = player.emoji
                return

        # Try vertical movement
        new_pos = player.position.copy()
        new_pos[1] += -1 if diff[1] < 0 else 1
        if (0 <= new_pos[1] < len(self.game_grid) and
            self.game_grid[new_pos[1]][player.position[0]] == BASE_TILE):
            # Valid vertical move
            self.game_grid[player.position[1]][player.position[0]] = BASE_TILE
            player.position[1] = new_pos[1]
            self.game_grid[player.position[1]][player.position[0]] = player.emoji
            return

        new_pos = player.position.copy()
        new_pos[0] += -1 if diff[0] < 0 else 1
        if (0 <= new_pos[0] < len(self.game_grid[0]) and
            self.game_grid[player.position[1]][new_pos[0]] == BASE_TILE):
            # Valid horizontal move
            self.game_grid[player.position[1]][player.position[0]] = BASE_TILE
            player.position[0] = new_pos[0]
            self.game_grid[player.position[1]][player.position[0]] = player.emoji
            return

        new_pos = player.position.copy()
        new_pos[1] += 1
        if (0 <= new_pos[1] < len(self.game_grid) and
            self.game_grid[new_pos[1]][player.position[0]] == BASE_TILE):
            # Valid vertical move
            self.game_grid[player.position[1]][player.position[0]] = BASE_TILE
            player.position[1] = new_pos[1]
            self.game_grid[player.position[1]][player.position[0]] = player.emoji
            return


class SingleTargetStatus(Cooldown):
    def __init__(self, name, emoji, stats, acted, entities):
        super().__init__(name, emoji, stats, self.attack, acted, entities=entities)


class SelfBuff(Cooldown):
    def __init__(self, name, emoji, stats, acted, entities, view: CombatView = None):
        view = view
        super().__init__(name, emoji, stats, self.attack, acted, entities=entities)


