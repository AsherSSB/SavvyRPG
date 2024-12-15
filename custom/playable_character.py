import custom.stattable as sts

class PlayableCharacter():
    def __init__(self, name, gender, race, origin):
        self.name:str = name
        self.gender:str = gender
        self.race:sts.Race = race
        self.origin:sts.Origin = origin
        self.stats = self.origin.stats + self.race.statmods

    def __str__(self):
        return f"Name: {self.name}\nGender: {self.gender}\nRace: {self.race}\nClass: {self.origin}\n{self.stats}"

