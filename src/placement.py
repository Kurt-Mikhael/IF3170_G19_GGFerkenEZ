class Placement:
    def __init__(self, position, orientation):
        self.position = position
        self.orientation = orientation

    def print(self):
        print(f"Placement(position={self.position}, orientation={self.orientation})")

    def rotate(self, axis):
        # rotasi 90° terhadap suatu sumbu = dua sumbu lainnya bertukar
        a, b = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}[axis]
        self.orientation = [
            b if s == a else a if s == b else s
            for s in self.orientation
        ]
