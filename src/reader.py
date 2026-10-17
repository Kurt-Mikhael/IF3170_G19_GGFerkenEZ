import json

from src.package import Package
from src.problem import Problem
from src.truck import Truck


def load_problem(path):
    with open(path) as f:
        data = json.load(f)
    td = data["truck"]["dimensions"]
    truck = Truck(td["w"], td["l"], td["h"], data["truck"]["max_capacity"])
    packages = [
        Package(p["id"], p["dimensions"]["w"], p["dimensions"]["l"], p["dimensions"]["h"],
                p["value"], p["weight"], p["is_fragile"], p["eta"])
        for p in data["packages"]
    ]
    return Problem(truck, packages)
