from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack
from custom.combat.entities import Entity, EntitiesInfo

BASE_TILE = ":green_square:"
# class WeaponStatTable():
#     dmg: int
#     spd: float
#     rng: int
#     cc: float
#     cm: float
#     acc: float
#     scalar: float
#     stat: str


class Cleave(AOEAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(
            dmg=12,
            spd=3,
            rng=1,
            cc=0.10,
            cm=1.5,
            acc=0.85,
            scalar=0.2,
            stat="str"
        )
        super().__init__(name="Cleave", emoji="🪓", stats=stats, acted="Cleaved", entities=entities)


class Execute(Cooldown):
    def __init__(self, entities: EntitiesInfo):
        stats = WeaponStatTable(
            dmg=5,
            spd=4,
            rng=1,
            cc=0.0,
            cm=1.0,
            acc=0.95,
            scalar=0.3,
            stat="str"
        )
        super().__init__(name="Execute", emoji="⚔", stats=stats, active=self.attack, acted="Executed", entities=entities)
        self.maxhps = [entity.hp for entity in entities.lst]

    def attack(self, target_indexes: list[int]):
        target_index = target_indexes[0]
        if self.miss():
            return f"{self.name} missed"
        mult = self.calculate_crit()
        mult = mult * self.maxhps[target_index] / self.entities.lst[target_index].hp
        dmg = int(self.stats.dmg * mult)
        self.entities.lst[target_index].hp -= dmg
        if self.entities.lst[target_index].hp <= 0:
            return f"{self.acted} {self.entities.lst[target_index].name}"
        return f"{self.name} hit {self.entities.lst[target_index].name} for {dmg}"


class LeapingStike(MovingSingleTargetAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(
            dmg=6, spd=3, rng=3, cc=0.1, cm=1.5, acc=0.7, scalar=0.2, stat="str"
        )
        super().__init__(name="Leaping Strike", emoji="🦵", stats=stats, acted="Stomped", entities=entities)

    def attack(self, target_indexes):
        while not self.in_range(self.entities.lst[self.entities.user_index], self.entities.lst[target_indexes[0]], 1):
            self.move_toward_enemy(target_indexes[0])
        return super().attack(target_indexes)

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


