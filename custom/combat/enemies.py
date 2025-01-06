from custom.combat.enemy import Enemy
from custom.combat.entities import NPCStatTable, Drops
from custom.combat.cooldown_base_classes import EnemyCooldown, WeaponStatTable


class TrainingDummy(Enemy):
    def __init__(self):
        self.name = "TrainingDummy"
        self.stats = NPCStatTable(120, 0.0, 0.0)
        self.drops = Drops(6, 9, None)
        self.attack = EnemyCooldown(name="Smack", stats=WeaponStatTable(
            dmg=1, spd=3, rng=1, cc=0.2, cm=2.0, acc=0.9, scalar=0.1, stat="str"))
        self.emoji = ":dizzy_face:"





