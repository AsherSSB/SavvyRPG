from typing import Callable
import random
from custom.playable_character import PlayableCharacter
from custom.gear import Weapon, WeaponStatTable
from custom.combat.entities import Entity, EntitiesInfo


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

    def attack(self, playerindex: int) -> str:
        if self.miss():
            return f"missed {self.name}"
        if random.random > self.entities.lst[playerindex].dodge:
            return f"{self.entities.lst[playerindex].name} dodged {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        self.entities.lst[playerindex].hp -= dmg
        return f"{hit} {self.entities.lst[playerindex].name} for {dmg} damage"


class SingleTargetAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)

    def attack(self, enemy:Entity) -> str:
        if self.miss():
            return f"missed {self.name}"
        if random.random > enemy.dodge:
            return f"{enemy.name} dodged {self.name}"
        mult = self.calculate_crit()
        hit = f"crit {self.acted}" if mult > 1.0 else self.acted
        dmg = int(self.stats.dmg * mult)
        enemy.hp -= dmg
        return f"{hit} {enemy.name} for {dmg} damage"
    
    
class AOEAttack(Cooldown):
    def __init__(self, name, emoji, stats, acted):
        super().__init__(name, emoji, stats, self.attack, acted)  
    
    def attack(self, entities: list[Entity]):
        message = {self.name}
        for entity in entities:
            if self.miss():
                message += f" missed {entity.name},"
                continue
            if random.random() < entity.dodge:
                message += f" was dodged by {entity.name},"
                continue
            mult = self.calculate_crit()
            dmg = int(self.stats.dmg * mult)
            entity.hp -= dmg
            message += f" hit {entity.name} for {dmg},"
        # remove trailing comma
        message = message[0:-1]
        return message