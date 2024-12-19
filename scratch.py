from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Cooldown:
    name: str
    emoji: str | None
    acted: str
    time: float
    active: Callable

hp = 10

mycd = Cooldown(name="Punch", emoji=":punch:", acted="punched", time=1.0, active=lambda target: target - 5)

newhp = mycd.active(hp)

print(hp, newhp)
