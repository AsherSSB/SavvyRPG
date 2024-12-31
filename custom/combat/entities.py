from dataclasses import dataclass
from custom.gear import Drops
from custom.combat.cooldown_base_classes import EnemyCooldown


@dataclass
class PlayerPracticalStats():
    dodge: float
    resistance: float


@dataclass
class Entity():
    name: str
    hp: int
    res: float
    dodge: float
    position: list[int]
    emoji: str


@dataclass
class NPCStatTable():
    hp: int
    resist: float
    dodge: float


@dataclass
class EntitiesInfo():
    lst: list[Entity]
    user_index: int
    player_count: int
    enemy_count: int


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, attack:EnemyCooldown, emoji: str):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.attack = attack
        self.emoji = emoji

