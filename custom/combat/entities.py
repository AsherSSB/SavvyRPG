from dataclasses import dataclass, field
from custom.base_items import Item


@dataclass
class Drops():
    xp: int
    gold: int
    item: Item | None


@dataclass
class PlayerPracticalStats():
    dodge: float = field(default=1.0, kw_only=True)
    resistance: float = field(default=1.0, kw_only=True)
    moves: int = field(default=3, kw_only=True)
    attacks: int = field(default=1, kw_only=True)
    healing: float = field(default=0.0, kw_only=True)
    multicast: float = field(default=0.0, kw_only=True)
    critchance: float = field(default=0.0, kw_only=True)
    critmult: float = field(default=0.0, kw_only=True)


@dataclass
class Entity():
    name: str
    hp: int
    res: float
    dodge: float
    position: list[int]
    emoji: str
    status: dict


@dataclass
class NPCStatTable():
    hp: int
    resist: float
    dodge: float
    moves: int


@dataclass
class EntitiesInfo():
    lst: list[Entity]
    user_index: int
    player_count: int
    enemy_count: int


