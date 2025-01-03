from custom.combat.cooldown_base_classes import SingleTargetAttack, AOEAttack, Cooldown
from custom.gear import WeaponStatTable
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
    def __init__(self):
        stats = WeaponStatTable(
            dmg=12,
            spd=3,
            rng=1,
            cc=0.10,
            cm=1.5,
            acc=0.85,
            scalar=0.8,
            stat="str"
        )
        super().__init__("Cleave", "🪓", stats, "Cleaved")


class Execute(Cooldown):
    def __init__(self, entities: EntitiesInfo):
        stats = WeaponStatTable(
            dmg=5,
            spd=4,
            rng=1,
            cc=0.0,
            cm=1.0,
            acc=0.95,
            scalar=1.0,
            stat="str"
        )
        super().__init__("Execute", "⚔", stats, "Executed", entities=entities)
        self.maxhps = [entity.hp for entity in entities]

    def attack(self, target_indexes: tuple[int]):
        target_index = target_indexes[0]
        if self.miss():
            return f"{self.name} missed"
        mult = self.calculate_crit()
        mult = mult * self.entities[target_index] / self.maxhps[target_index]
        dmg = int(self.stats.dmg * mult)
        self.entities[target_index].hp -= dmg
        if self.entities[target_index].hp <= 0:
            return f"{self.acted} {self.entities[target_index].name}"
        return f"{self.name} hit {self.entities[target_index].name} for {dmg}"


