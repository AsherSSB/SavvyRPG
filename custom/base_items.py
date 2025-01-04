from dataclasses import dataclass, field


@dataclass
class Item():
    name: str
    emoji: str = field(default="💁‍♀️", kw_only=True)
    value: int = field(default=0, kw_only=True)
    stack_size: int = field(default=1, kw_only=True)
    quantity: int = field(default=1, kw_only=True)


