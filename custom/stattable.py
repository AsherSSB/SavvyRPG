class StatTable():
    def __init__(self, str, wil, dex, int, att):
        self.str = str
        self.wil = wil
        self.dex = dex
        self.int = int
        self.att = att

    def __str__(self):
        return f"""Stats:
Strength: {self.str}
Will: {self.wil}
Dexterity: {self.dex}
Intelligence: {self.int}
Attunement: {self.att}"""
    

class Nomad():
    def __init__(self):
        self.stats = StatTable(11, 14, 11, 8, 8)

    def __str__(self):
        return f"""
# Nomad

Nomads are lone wanderers, forged by their hardships. These eduring \
and well-rounded survivalists seek adventure to test their strength and \
resolve. Whether by the bite of a heavy sword or the thrill of navigating \
treacherous lands, they are driven by the desire to prove themselves against \
the challenges of the world. With few ties to any one place, they embrace a \
life of freedom, their resourcefulness and resilience their greatest assets. \
Adaptable and tough, the Nomad is a true testament to endurance, ever seeking \
the next trial that will push them to their limits.

Base {self.stats}"""


class Barbarian():
    def __init__(self):
        self.stats = StatTable(16, 13, 7, 6, 10)

    def __str__(self):
        return f"""
# Barbarian

Barbarians are the embodiment of unrelenting rage and raw power, their very \
existence defined by the relentless pursuit of dominance. Driven by a primal \
hunger for conquest, they are fueled by an insatiable thirst for violence and \
destruction, their battle cries echoing across the lands. With every swing of \
their weapons, they carve through their enemies, \
their fury unstoppable. These fearless warriors know no mercy, maiming and \
slaughtering all who dare to stand in their path.

Base {self.stats}"""
 

class Bard():
    def __init__(self):
        self.stats = StatTable(8, 8, 13, 13, 11)

    def __str__(self):
        return f"""
# Bard

Base {self.stats}"""

class Rogue():
    def __init__(self):
        self.stats = StatTable(7, 6, 16, 9, 14)

    def __str__(self):
        return f"""
# Rogue

Base {self.stats}"""

class Ranger():
    def __init__(self):
        self.stats = StatTable(8, 8, 14, 10, 12)

    def __str__(self):
        return f"""
# Ranger

Base {self.stats}"""

class Wizard():
    def __init__(self):
        self.stats = StatTable(7, 9, 8, 16, 12)

    def __str__(self):
        return f"""
# Wizard

Base {self.stats}"""

class Human():
    def __init__(self):
        self.statmods = StatTable(0, 2, -1, 1, -1)
    
    def __str__(self):
        return f"""
# Human

Willful and curious, Humans are known for their tribal nature and unbreakable \
spirit. One of the races local to Aether, they have created kingdoms and \
monuments in their image, shining beacons of their ability to collaborate \
and shape the world around them. A versitile bunch, humans are reguarded as a \
good addition to any group, boasting strong physical capacity, loyalty, and an \
unsatiable thirst for knowledge, though they are prone to awkward and clumsy \
errors.

Bonus {self.statmods}"""


class NotHuman():
    def __init__(self):
        self.statmods = StatTable(-5, -5, -5, -5, -5)

    def __str__(self):
        return f"# Not Human \n\nWhy would you ever pick a non-human? Humans are superior in every way!\n(This is a placeholder)\n\n\"Bonus\" {self.statmods}"