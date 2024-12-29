from dataclasses import dataclass, field
from cogs.combat import Cooldown


@dataclass
class Item():
    name: str
    emoji: str = field(default="💁‍♀️", kw_only=True)
    value: int = field(default=0, kw_only=True)
    stack_size: int = field(default=1, kw_only=True)
    quantity: int = field(default=1, kw_only=True)


@dataclass
class WeaponStatTable():
    dmg: int
    spd: float
    rng: int
    cc: float
    cm: float
    acc: float
    scalar: float
    stat: str


@dataclass
class Weapon(Item):
    cooldown: Cooldown
    scale: str
    slots: int = field(default=2, kw_only=True)


@dataclass
class Drops():
    xp: int
    gold: int
    item: Item | None


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
    dodge: float | None
    bonus_stats: BonusStatsTable


@dataclass
class Gear(Item):
    rarity: str
    stats: GearStatTable


@dataclass
class HeadGear(Gear):
    critchance: float | None = field(default=None, kw_only=True)
    multicast: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 5, .05)
        super().__init__(name, rarity, stats, value=value)


@dataclass
class ChestGear(Gear):
    healing: float | None = field(default=None, kw_only=True)
    attacks: int | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.2, 10, 0.1)
        super().__init__(name, rarity, stats, value=value)


@dataclass
class HandGear(Gear):
    critmult: float | None = field(default=None, kw_only=True)
    attacks: int | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.03)
        super().__init__(name, rarity, stats, value=value)


@dataclass
class LegGear(Gear):
    healing: float | None = field(default=None, kw_only=True)
    critmult: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.1, 10, 0.05)
        super().__init__(name, rarity, stats, value=value)


@dataclass
class FootGear(Gear):
    moves: int | None = field(default=None, kw_only=True)
    critchance: float | None = field(default=None, kw_only=True)

    def __init__(self, name, rarity, value, stats=None):
        if stats == None:
            stats = self.randomize_gear_stats(0.05, 5, 0.1)
        super().__init__(name, rarity, stats, value=value)
