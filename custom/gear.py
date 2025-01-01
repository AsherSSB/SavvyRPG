from dataclasses import dataclass, field
from custom.combat.cooldown_base_classes import Cooldown
from custom.base_items import Item

@dataclass
class Weapon(Item):
    cooldown: Cooldown
    scale: str
    slots: int = field(default=2, kw_only=True)


@dataclass
class BonusStatsTable():
    strength: int | None = field(default=None, kw_only=True)
    will: int | None = field(default=None, kw_only=True)
    dexterity: int | None = field(default=None, kw_only=True)
    intelligence: int | None = field(default=None, kw_only=True)
    attunement: int | None = field(default=None, kw_only=True)


@dataclass
class GearStatTable():
    resist: float 
    maxhp: int
    dodge: float 
    bonus_stats: BonusStatsTable


@dataclass
class Gear(Item):
    rarity: str
    stats: GearStatTable


@dataclass
class HeadGear(Gear):
    critchance: float | None = field(default=None, kw_only=True)
    multicast: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats):
        super().__init__(name, rarity, stats, value=value)


@dataclass
class ChestGear(Gear):
    healing: float | None = field(default=None, kw_only=True)
    attacks: int | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats):
        super().__init__(name, rarity, stats, value=value)


@dataclass
class HandGear(Gear):
    critmult: float | None = field(default=None, kw_only=True)
    attacks: int | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats):
        super().__init__(name, rarity, stats, value=value)


@dataclass
class LegGear(Gear):
    healing: float | None = field(default=None, kw_only=True)
    critmult: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats):
        super().__init__(name, rarity, stats, value=value)


@dataclass
class FootGear(Gear):
    moves: int | None = field(default=None, kw_only=True)
    critchance: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats):
        super().__init__(name, rarity, stats, value=value)
