from dataclasses import dataclass, field
from custom.combat.cooldown_base_classes import Cooldown, SingleTargetAttack
from custom.base_items import Item


@dataclass
class Weapon(Item):
    cooldown: SingleTargetAttack
    slots: int = field(default=2, kw_only=True)


@dataclass
class BonusStatsTable():
    strength: int = field(default=0, kw_only=True)
    will: int = field(default=0, kw_only=True)
    dexterity: int = field(default=0, kw_only=True)
    intelligence: int = field(default=0, kw_only=True)
    attunement: int = field(default=0, kw_only=True)


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
    critchance: float | None = field(default=0.0, kw_only=True)
    multicast: float | None = field(default=0.0, kw_only=True)


@dataclass
class ChestGear(Gear):
    healing: float | None = field(default=0.0, kw_only=True)
    attacks: int | None = field(default=0, kw_only=True)


@dataclass
class HandGear(Gear):
    critmult: float | None = field(default=0.0, kw_only=True)
    attacks: int | None = field(default=0, kw_only=True)


@dataclass
class LegGear(Gear):
    healing: float | None = field(default=0.0, kw_only=True)
    critmult: float | None = field(default=0.0, kw_only=True)


@dataclass
class FootGear(Gear):
    moves: int | None = field(default=0, kw_only=True)
    critchance: float | None = field(default=0.0, kw_only=True)


@dataclass
class Loadout():
    head: HeadGear | None
    chest: ChestGear | None
    hands: HandGear | None
    legs: LegGear | None
    feet: FootGear | None
    weapon: Weapon | None


