from custom.gear import Weapon
from custom.combat.cooldown_base_classes import SingleTargetAttack, WeaponStatTable


class Greatsword(Weapon):
    def __init__(self):
        stats = WeaponStatTable(dmg=10, spd=1, rng=2, cc=0.2, cm=2.0, acc=0.8, scalar=0.2, stat="str")
        self.cooldown = SingleTargetAttack(name="Slash", emoji="⚔", stats=stats, acted="slashed", entities=None)

# • Sword + Shield
# • Greatsword/Great Hammer
# • Dual Swords
# • Bow + Arrow
# • Spear/Lance/Halbert
# • Katana
# • Magic Tomes (Elemental) (Heal)
