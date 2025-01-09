from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack, SingleTargetStatus
from custom.combat.entities import Entity, EntitiesInfo


# name emoji stats acted entities
class ThrowingKnife(SingleTargetAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(dmg=11, spd=2, rng=3, cc=0.25, cm=1.75, acc=0.8, scalar=0.2, stat="dex")
        super().__init__(name="Throwing Knife", emoji="🗡️", stats=stats, acted="struck", entities=entities)


class PocketSand(SingleTargetStatus):
    def __init__(self, entities):
        stats = WeaponStatTable(dmg=2, spd=3, rng=1, cc=0.1, cm=1.25, acc=0.9, scalar=0.1, stat="dex")
        super().__init__(name="Pocket Sand", emoji="✨", stats=stats, acted="blinded", entities=entities)

    def attack(self, targets: list[list]):
        user_stats = self.entities.lst[self.entities.user_index].status
        if "blinded" not in user_stats:
            user_stats["blinded"] = 3
        else:
            user_stats["blinded"] += 3
        return f"{self.entities.lst[self.entities.user_index].name} used {self.name}"


