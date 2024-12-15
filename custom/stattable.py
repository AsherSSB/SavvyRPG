class StatTable():
    def __init__(self):
        self.str:int
        self.wil:int
        self.dex:int
        self.int:int
        self.att:int
    

class Barbarian():
    def __init__(self):
        self.stats = StatTable()
        self.stats.str = 16
        self.stats.wil = 13
        self.stats.dex = 7
        self.stats.int = 6
        self.stats.att = 10


class Bard():
    def __init__(self):
        self.stats = StatTable()
        self.stats.str = 8
        self.stats.wil = 8
        self.stats.dex = 13
        self.stats.int = 13
        self.stats.att = 11


class Rogue():
    def __init__(self):
        self.stats = StatTable()
        self.stats.str = 7
        self.stats.wil = 6
        self.stats.dex = 16
        self.stats.int = 9
        self.stats.att = 14


class Ranger():
    def __init__(self):
        self.stats = StatTable()
        self.stats.str = 8
        self.stats.wil = 8
        self.stats.dex = 14
        self.stats.int = 10
        self.stats.att = 12


class Wizard():
    def __init__(self):
        self.stats = StatTable()
        self.stats.str = 7
        self.stats.wil = 9
        self.stats.dex = 8
        self.stats.int = 16
        self.stats.att = 12