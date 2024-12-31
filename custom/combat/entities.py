from dataclasses import dataclass
from custom.base_items import Item


@dataclass
class Drops():
    xp: int
    gold: int
    item: Item | None


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


