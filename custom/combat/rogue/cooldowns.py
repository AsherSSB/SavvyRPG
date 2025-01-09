from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack, SingleTargetStatus, SelfBuff
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
        enemy_status = self.entities.lst[targets[0]].status
        if "blinded" not in enemy_status:
            enemy_status["blinded"] = 3
        else:
            enemy_status["blinded"] += 3
        return f"{self.entities.lst[self.entities.user_index].name} used {self.name} on {self.entities.lst[targets[0]].name}"


class Sprint(SelfBuff):
    def __init__(self, entities):
        stats = WeaponStatTable(dmg=0, spd=5, rng=99, cc=0.0, cm=0.0, acc=1.0, scalar=0.4, stat="att")
        super().__init__(name="Sprint", emoji="🦶", stats=stats, acted="sped up", entities=entities)

    def attack(self):
        user_stats = self.entities.lst[self.entities.user_index].status
        if "fast" not in user_stats:
            user_stats["fast"] = 3
        else:
            user_stats["fast"] += 3
        return f"{self.entities.lst[self.entities.user_index].name} used {self.name}"


class Disembowel(SingleTargetAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(dmg=13, spd=5, rng=1, cc=1.0, cm=3.0, acc=0.9, scalar=0.3, stat="dex")
        super().__init__(name="Disembowel", emoji="🫀", stats=stats, acted="disemboweled", entities=entities)
        self.maxhps = [entity.hp for entity in entities.lst]

    def attack(self, target_indexes: list[int]):
        target_index = target_indexes[0]
        if self.miss():
            return f"{self.name} missed"
        mult = self.stats.cm * self.entities.lst[target_index].hp / self.maxhps[target_index]
        dmg = int(self.stats.dmg * mult)
        self.entities.lst[target_index].hp -= dmg
        return f"{self.acted} {self.entities.lst[target_index].name} for {dmg} damage"


