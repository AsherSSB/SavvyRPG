from custom.combat.enemy import Enemy
from custom.combat.entities import NPCStatTable, Drops
from custom.combat.cooldown_base_classes import EnemyCooldown, WeaponStatTable


class TrainingDummy(Enemy):
    def __init__(self):
        self.name = "TrainingDummy"
        self.stats = NPCStatTable(120, 0.0, 0.0, 1)
        self.drops = Drops(6, 9, None)
        self.attack = EnemyCooldown(name="Smack", stats=WeaponStatTable(
            dmg=1, spd=3, rng=1, cc=0.2, cm=2.0, acc=0.9, scalar=0.1, stat="str"))
        self.emoji = ":dizzy_face:"


class Wolf(Enemy):
    def __init__(self):
        self.name = "Wolf"
        self.stats = NPCStatTable(80, 0.1, 0.2, 3)  # Less HP but high dodge
        self.drops = Drops(8, 12, None)
        self.attack = EnemyCooldown(name="Bite", stats=WeaponStatTable(
            dmg=8, spd=4, rng=1, cc=0.15, cm=1.8, acc=0.85, scalar=0.15, stat="str"))
        self.emoji = ":wolf:"


class Bandit(Enemy):
    def __init__(self):
        self.name = "Bandit"
        self.stats = NPCStatTable(100, 0.15, 0.15, 2)  # Balanced stats
        self.drops = Drops(10, 20, None)
        self.attack = EnemyCooldown(name="Slash", stats=WeaponStatTable(
            dmg=10, spd=3, rng=2, cc=0.2, cm=1.5, acc=0.9, scalar=0.2, stat="str"))
        self.emoji = ":supervillain:"


class Skeleton(Enemy):
    def __init__(self):
        self.name = "Skeleton"
        self.stats = NPCStatTable(70, 0.3, 0.05, 1)  # High resist, low dodge
        self.drops = Drops(12, 15, None)
        self.attack = EnemyCooldown(name="Bone Strike", stats=WeaponStatTable(
            dmg=12, spd=2, rng=1, cc=0.1, cm=1.7, acc=0.8, scalar=0.1, stat="str"))
        self.emoji = ":skull:"


class DarkMage(Enemy):
    def __init__(self):
        self.name = "Dark Mage"
        self.stats = NPCStatTable(90, 0.2, 0.1, 1)
        self.drops = Drops(15, 25, None)
        self.attack = EnemyCooldown(name="Shadow Bolt", stats=WeaponStatTable(
            dmg=15, spd=2, rng=3, cc=0.25, cm=2.0, acc=0.85, scalar=0.25, stat="int"))
        self.emoji = ":mage:"


class Golem(Enemy):
    def __init__(self):
        self.name = "Stone Golem"
        self.stats = NPCStatTable(200, 0.4, 0.0, 2)  # Very high HP and resist, no dodge
        self.drops = Drops(20, 30, None)
        self.attack = EnemyCooldown(name="Rock Throw", stats=WeaponStatTable(
            dmg=20, spd=1, rng=2, cc=0.05, cm=1.5, acc=0.75, scalar=0.3, stat="str"))
        self.emoji = ":moyai:"


