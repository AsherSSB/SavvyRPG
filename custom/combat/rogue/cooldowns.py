from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack, SingleTargetStatus
from custom.combat.entities import Entity, EntitiesInfo


# name emoji stats acted entities
class ThrowingKnife(SingleTargetAttack):
    def __init__(self):
        stats = WeaponStatTable(dmg=11, spd=2, rng=3, cc=0.25, cm=1.75, acc=0.8, scalar=0.2, stat="dex")
        super().__init__(name="Throwing Knife", emoji="🗡️", stats=stats, acted="struck")
