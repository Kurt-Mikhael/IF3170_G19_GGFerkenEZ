ORIENTATIONS = [
    ("x", "y", "z"),
    ("x", "z", "y"),
    ("y", "x", "z"),
    ("z", "x", "y"),
    ("y", "z", "x"),
    ("z", "y", "x"),
]


class Package:
    def __init__(self, id, w, l, h, value, weight, is_fragile, eta):
        self.id = id
        self.w = w
        self.l = l
        self.h = h
        self.value = value
        self.weight = weight
        self.is_fragile = is_fragile
        self.eta = eta

    def print(self):
        print(f"Package(id={self.id}, dims=({self.w},{self.l},{self.h}), value={self.value}, weight={self.weight}, fragile={self.is_fragile}, eta={self.eta})")

    def effective_dims(self, orientation):
        w_axis, l_axis, h_axis = orientation
        size = {w_axis: self.w, l_axis: self.l, h_axis: self.h}
        return (size["x"], size["y"], size["z"])
