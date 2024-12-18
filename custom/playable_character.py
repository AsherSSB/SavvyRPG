import custom.stattable as sts

class PlayableCharacter():
    def __init__(self, name, gender, race, origin, stats:sts.StatTable = None, xp = 0, gold = 0):
        self.name:str = name
        self.gender:str = gender
        self.race:sts.Race = race
        self.origin:sts.Origin = origin
        self.stats:sts.StatTable = stats if stats != None else self.origin.stats + self.race.statmods
        self.xp:int = xp
        self.gold:int = gold
        self.level:int = self.calculate_level()

    def calculate_level(self):
        return int((self.xp // 100) ** (3/7))
    
    def add_xp(self, amount):
        self.xp += amount
        new_level = self.calculate_level()
        if new_level > self.level and new_level <= 50:
            self.level_up(new_level)

    def level_up(self, new_level):
        self.level = new_level

    def xp_for_next_level(self):
        next_level = self.level + 1
        current_level_xp = int((self.level ** (3/7)) * 100)
        next_level_xp = int((next_level ** (3/7)) * 100)
        return next_level_xp - current_level_xp
    
    def level_progress(self):
        current_level_xp = int((self.level ** (3/7)) * 100)
        return int(self.xp - current_level_xp)
        

    def __str__(self):
        return f"Name: {self.name}\nGender: {self.gender}\nRace: {self.race}\nClass: {self.origin}\n\n{self.stats}"

