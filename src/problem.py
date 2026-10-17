class Problem:
    def __init__(self, truck, packages):
        self.truck = truck
        self.packages = packages
        self.package_map = {p.id: p for p in packages}

    def print(self):
        self.truck.print()
        for p in self.packages:
            p.print()
