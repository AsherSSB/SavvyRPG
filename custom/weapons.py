class Weapon:
    def __init__(self, dmg, rng, cc, cm, acc, slots):
        self.dmg:int = dmg
        self.rng:int = rng
        self.cc:float = cc
        self.cm:float = cm
        self.acc:float = acc
        self.slots:int = slots

    def __str__(self):
        return f"""
Weapon Stats:
Damage: {self.dmg}
Range: {self.rng}
Crit Chance: {self.cc}
Crit Multiplier: {self.cm}
Accuracy: {self.acc}
Slots: {self.slots} Handed"""

class Sword(Weapon):
    def __init__(self):
        super().__init__(5, 1, 0.1, 2.0, 0.95, 1)


class Shield(Weapon):
    def __init__(self, defense):
        super().__init__(0, 0, 0, 0, 0, 1)
        self.defense = defense
    
    def __str__(self):
        return (super().__str__() + f"\nDefense: +{self.defense}")
    


# • Sword + Shield
# • Greatsword/Great Hammer
# • Dual Swords
# • Bow + Arrow
# • Spear/Lance/Halbert 
# • Katana
# • Magic Tomes (Elemental) (Heal)