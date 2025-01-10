from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack, SingleTargetStatus, SelfBuff
from custom.combat.entities import Entity, EntitiesInfo


class MeteorShower(AOEAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(dmg=15, spd=5, rng=3, cc=0.05, cm=1.25, acc=0.95, scalar=0.3, stat="int")
        super().__init__(name="MeteorShower", emoji="🪨", stats=stats, acted="rained upon", entities=entities)
