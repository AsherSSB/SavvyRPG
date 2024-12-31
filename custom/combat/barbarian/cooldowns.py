from custom.combat.cooldown_base_classes import Cooldown, SingleTargetAttack, AOEAttack
from custom.gear import WeaponStatTable
from custom.combat.entities import Entity
import random

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
    def __init__(self):
        stats = WeaponStatTable(
            dmg=12,
            spd=3,
            rng=1,
            cc=1.0,
            cm=1.5,
            acc=0.85,
            scalar=0.8,
            stat="str"
        )
        super().__init__("Cleave", "🪓", stats, "Cleaved")