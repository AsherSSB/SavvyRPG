class StatTable():
    def __init__(self, str, wil, dex, int, att):
        self.str = str
        self.wil = wil
        self.dex = dex
        self.int = int
        self.att = att

    def __str__(self):
        return f"""\
Strength: {self.str}
Will: {self.wil}
Dexterity: {self.dex}
Intelligence: {self.int}
Attunement: {self.att}"""

    def __add__(self, other):
        return StatTable(
            self.str + other.str,
            self.wil + other.wil,
            self.dex + other.dex,
            self.int + other.int,
            self.att + other.att
        )

    def to_dict(self):
        return {
            "str": self.str,
            "wil": self.wil,
            "dex": self.dex,
            "int": self.int,
            "att": self.att
        }


class Origin():
    def __init__(self):
        self.stats:StatTable
        self.description:str


class Nomad(Origin):
    def __init__(self):
        self.stats = StatTable(11, 14, 11, 8, 8)
        self.description = f"""
# Nomad

Nomads are lone wanderers, forged by their hardships. These eduring \
and well-rounded survivalists seek adventure to test their strength and \
resolve. Whether by the bite of a heavy sword or the thrill of navigating \
treacherous lands, they are driven by the desire to prove themselves against \
the challenges of the world. With few ties to any one place, they embrace a \
life of freedom, their resourcefulness and resilience their greatest assets. \
Adaptable and tough, the Nomad is a true testament to endurance, ever seeking \
the next trial that will push them to their limits.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Nomad"


class Barbarian(Origin):
    def __init__(self):
        self.stats = StatTable(16, 13, 7, 6, 10)
        self.description = f"""
# Barbarian

Barbarians are the embodiment of unrelenting rage and raw power, their very \
existence defined by the relentless pursuit of dominance. Driven by a primal \
hunger for conquest, they are fueled by an insatiable thirst for violence and \
destruction, their battle cries echoing across the lands. With every swing of \
their weapons, they carve through their enemies, \
their fury unstoppable. These fearless warriors know no mercy, maiming and \
slaughtering all who dare to stand in their path.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Barbarian"


class Bard(Origin):
    def __init__(self):
        self.stats = StatTable(8, 8, 13, 13, 11)
        self.description = f"""
# Bard

Bards are whimsical and versitile, treating every encounter as another chance \
to perform and show off. Through the power of music, they buff their allies \
with war songs and encouragement while weakening their foes with mockery and \
curses. Bards also carry a mental encyclopedia of bardic knowledge, able to \
recount tales and adventures of the past. Do not be fooled however, as they \
are just as capable at handling themselves and fighting off enemies on their \
own. Versitile and positive, a Bard is a welcome addition to any party.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Bard"


class Rogue(Origin):
    def __init__(self):
        self.stats = StatTable(7, 6, 16, 9, 14)
        self.description = f"""
# Rogue

Rogues are daring coldblooded killers who rely on precision, agility, and \
cunning to eliminate their foes with ruthless efficiency. Masters of stealth \
and deception, rogues use their keen instincts and \
deadly skills to turn the tide of any encounter. Whether as skilled assassins, \
or sly thieves, rogues navigate dangerous situations with a \
mix of clever tricks and lethal force. Their quick reflexes and unparalleled \
adaptability allow them to exploit the weaknesses of their enemies, making \
them feared adversaries in combat and invaluable allies in any covert operation.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Rogue"


class Ranger(Origin):
    def __init__(self):
        self.stats = StatTable(8, 8, 14, 10, 12)
        self.description = f"""
# Ranger

Rangers are nimble and resourceful warriors who thrive in the wild, using \
their keen senses, survival instincts, and unmatched adaptability to \
overcome any challenge. Masters of both bow and blade, they excel at striking \
from a distance or engaging in close combat when necessary. Rangers are expert \
trackers and scouts, able to navigate treacherous terrain and hunt their prey \
with precision. Whether lining up the perfect shot, setting traps, or stalking \
their enemies, rangers rely on their sharp instincts, survival skills, and \
unmatched knowledge of the land to outlast and outmaneuver their foes.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Ranger"


class Wizard(Origin):
    def __init__(self):
        self.stats = StatTable(7, 9, 8, 16, 12)
        self.description = f"""
# Wizard

Wizards are scholars who devote their lives to the pursuit of knowledge and \
mastery of the arcane arts. Through rigorous study and discipline, wizards \
unlock the secrets of magic, bending reality to their will with carefully \
prepared spells. They wield their vast intellect to understand the \
fundamental forces of the world and harness them in battle. Wizards rely on \
spellbooks to store their hard-earned knowledge, and their power grows as they \
uncover new spells and delve deeper into arcane mysteries. Whether deciphering \
ancient tomes, unraveling curses, or unleashing devastating spells, wizards \
are the embodiment of magical proficiency and unparalleled intellect.

Base Stats:\n{self.stats}"""

    def __str__(self):
        return "Wizard"


class Race():
    def __init__(self):
        self.statmods:StatTable
        self.description:str


class Human(Race):
    def __init__(self):
        self.statmods = StatTable(1, 2, -1, 0, -1)
        self.description = f"""
# Human

Willful and curious, Humans are known for their tribal nature and unbreakable \
spirit. One of the races local to Aether, they have created kingdoms and \
monuments in their image, shining beacons of their ability to collaborate \
and shape the world around them. A versitile bunch, humans are reguarded as a \
good addition to any group, boasting strong physical capacity, loyalty, and an \
unsatiable thirst for knowledge, though they are prone to awkward and clumsy \
errors.

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Human"


class HighElf(Race):
    def __init__(self):
        self.statmods = StatTable(-2, -1, 0, 2, 2)
        self.description = f"""
# High Elf

Discerning and graceful, High Elves are known for their vast knowledge of and \
strong connection with nature. A race local to Aether, they are tall and \
beautiful beings with pointed ears whos lifespan lasts many times that of a \
human. Most High Elves devote their long lives to the persuit of knowledge, \
living in the Ancient Forests while studying the physical and arcane. \
Although preferring deplomacy, they are also very capable warriors, trained \
to protect themselves and others using percise and deadly blows.

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "High Elf"


class DarkElf(Race):
    def __init__(self):
        self.statmods = StatTable(-1, 1, 0, 2, -1)
        self.description = f"""
# Dark Elf

...

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Dark Elf"


class Dwarf(Race):
    def __init__(self):
        self.statmods = StatTable(2, 2, -2, 0, -1)
        self.description = f"""
# Dwarf

...

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Dwarf"


class Orc(Race):
    def __init__(self):
        self.statmods = StatTable(3, 1, -2, -1, 0)
        self.description = f"""
# Orc

...

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Orc"


class Fairy(Race):
    def __init__(self):
        self.statmods = StatTable(-2, -2, 1, 2, 2)
        self.description = f"""
# Fairy

...

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Fairy"


class Damned(Race):
    def __init__(self):
        self.statmods = StatTable(1, 3, -3, 2, -2)
        self.description = f"""
# Damned

...

Bonus Stats:\n{self.statmods}"""

    def __str__(self):
        return "Damned"


class OriginsInfo():
    def __init__(self):
        self.origins:set = {Nomad(), Bard(), Barbarian(), Rogue(), Ranger(), Wizard()}
        self.races:set = {Human(), HighElf(), Dwarf(), DarkElf(), Orc(), Fairy(), Damned()}

