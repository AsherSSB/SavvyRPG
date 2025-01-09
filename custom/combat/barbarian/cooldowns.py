from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown, WeaponStatTable, MovingSingleTargetAttack, SingleTargetStatus, SelfBuff
from custom.combat.entities import Entity, EntitiesInfo

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
    def __init__(self, entities):
        stats = WeaponStatTable(
            dmg=12,
            spd=3,
            rng=1,
            cc=0.10,
            cm=1.5,
            acc=0.85,
            scalar=0.2,
            stat="str"
        )
        super().__init__(name="Cleave", emoji="🪓", stats=stats, acted="Cleaved", entities=entities)


class Execute(Cooldown):
    def __init__(self, entities: EntitiesInfo):
        stats = WeaponStatTable(
            dmg=5,
            spd=4,
            rng=1,
            cc=0.0,
            cm=1.0,
            acc=0.95,
            scalar=0.3,
            stat="str"
        )
        super().__init__(name="Execute", emoji="⚔", stats=stats, active=self.attack, acted="Executed", entities=entities)
        self.maxhps = [entity.hp for entity in entities.lst]

    def attack(self, target_indexes: list[int]):
        target_index = target_indexes[0]
        if self.miss():
            return f"{self.name} missed"
        mult = self.calculate_crit()
        mult = mult * self.maxhps[target_index] / self.entities.lst[target_index].hp
        dmg = int(self.stats.dmg * mult)
        self.entities.lst[target_index].hp -= dmg
        if self.entities.lst[target_index].hp <= 0:
            return f"{self.acted} {self.entities.lst[target_index].name}"
        return f"{self.name} hit {self.entities.lst[target_index].name} for {dmg}"


class LeapingStike(MovingSingleTargetAttack):
    def __init__(self, entities):
        stats = WeaponStatTable(
            dmg=6, spd=3, rng=3, cc=0.1, cm=1.5, acc=0.7, scalar=0.2, stat="str"
        )
        super().__init__(name="Leaping Strike", emoji="🦵", stats=stats, acted="Stomped", entities=entities)

    def attack(self, target_indexes):
        while not self.in_range(self.entities.lst[self.entities.user_index], self.entities.lst[target_indexes[0]], 1):
            self.move_toward_enemy(target_indexes[0])
        # this actually deals damage to the enemy
        return super().attack(target_indexes)


class SavageShout(SelfBuff):
    def __init__(self, entities):
        stats=WeaponStatTable(dmg=0, spd=5, rng=99, cc=0.0, cm=0.0, acc=1.0, scalar=0.4, stat="att")
        super().__init__(name="SavageShout", emoji="🗣️", stats=stats, acted="Shouted", entities=entities)

    def attack(self):
        user_stats = self.entities.lst[self.entities.user_index].status
        if "enraged" not in user_stats:
            user_stats["enraged"] = 3
        else:
            user_stats["enraged"] += 3
        return f"{self.entities.lst[self.entities.user_index].name} used {self.name}"


