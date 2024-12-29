from typing import Callable
import random
from custom.playable_character import PlayableCharacter
from custom.gear import Weapon, WeaponStatTable
from custom.combat.entities import Entity

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