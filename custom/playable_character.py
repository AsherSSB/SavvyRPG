import custom.stattable as sts

class PlayableCharacter():
    def __init__(self, name, gender, race, origin):
        self.name:str = name
        self.gender:str = gender
        self.race:sts.Race = race
        self.origin:sts.Origin = origin
        self.stats = self.origin.stats + self.race.statmods

    def __str__(self):
        return f"{self.gender} {self.name}\n{self.race}\n\n{self.origin}"

