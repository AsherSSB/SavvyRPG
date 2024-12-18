from dataclasses import dataclass, field

@dataclass
class Person:
    name: str
    age: int = field(default=20,kw_only=True)

@dataclass
class Employee(Person):
    salary: float
    city: str = "New York"

# Create an Employee instance
emp = Employee(name="John", salary=100000)

print(emp)