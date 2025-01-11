from custom.gear import Weapon
from custom.combat.cooldown_base_classes import SingleTargetAttack, WeaponStatTable


class Fists(Weapon):
    def __init__(self):
        self.name = "Fists"
        self.emoji = "👊"
        stats = WeaponStatTable(dmg=8, spd=1, rng=1, cc=0.1, cm=1.5, acc=0.9, scalar=0.3, stat="str")
        self.cooldown = SingleTargetAttack(name="Punch", emoji="👊", stats=stats, acted="punched", entities=None)


class Greatsword(Weapon):
    def __init__(self):
        self.name = "Greatsword"
        self.emoji = "⚔"
        stats = WeaponStatTable(dmg=13, spd=1, rng=2, cc=0.2, cm=2.0, acc=0.9, scalar=0.2, stat="str")
        self.cooldown = SingleTargetAttack(name="Slash", emoji="⚔", stats=stats, acted="slashed", entities=None)

# • Sword + Shield
# • Greatsword/Great Hammer
# • Dual Swords
# • Bow + Arrow
# • Spear/Lance/Halbert
# • Katana
# • Magic Tomes (Elemental) (Heal)
