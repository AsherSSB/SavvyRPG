# I fucking hate circular dependancies
from custom.combat.cooldown_base_classes import EnemyCooldown
from custom.combat.entities import NPCStatTable, Drops


class Enemy():
    def __init__(self, name:str, stats:NPCStatTable, drops:Drops, attack:EnemyCooldown, emoji: str):
        self.name = name
        self.stats = stats
        self.drops = drops
        self.attack = attack
        self.emoji = emoji


