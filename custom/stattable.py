class StatTable():
    def __init__(self, str, wil, dex, int, att):
        self.str = str
        self.wil = wil
        self.dex = dex
        self.int = int
        self.att = att
    
class Nomad():
    def __init__(self):
        self. stats = StatTable(12, 14, 10, 8, 8)


class Barbarian():
    def __init__(self):
        self.stats = StatTable(16, 13, 7, 6, 10)


class Bard():
    def __init__(self):
        self.stats = StatTable(8, 8, 13, 13, 11)


class Rogue():
    def __init__(self):
        self.stats = StatTable(7, 6, 16, 9, 14)


class Ranger():
    def __init__(self):
        self.stats = StatTable(8, 8, 14, 10, 12)


class Wizard():
    def __init__(self):
        self.stats = StatTable(7, 9, 8, 16, 12)

