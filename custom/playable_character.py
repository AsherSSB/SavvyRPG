import custom.stattable as sts

class PlayableCharacter():
    def __init__(self, name, gender, race, origin, stats:sts.StatTable = None, xp = 0):
        self.name:str = name
        self.gender:str = gender
        self.race:sts.Race = race
        self.origin:sts.Origin = origin
        self.stats:sts.StatTable = stats if stats != None else self.origin.stats + self.race.statmods
        self.xp:int = xp

    def __str__(self):
        return f"Name: {self.name}\nGender: {self.gender}\nRace: {self.race}\nClass: {self.origin}\n\n{self.stats}"

