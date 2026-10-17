class Truck:
    def __init__(self, w, l, h, max_capacity):
        self.w = w
        self.l = l
        self.h = h
        self.max_capacity = max_capacity

    def print(self):
        print(f"Truck(w={self.w}, l={self.l}, h={self.h}, max_capacity={self.max_capacity})")
