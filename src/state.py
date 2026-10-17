from src.placement import Placement


class State:
    def __init__(self, placements):
        self.placements = placements

    def print(self):
        print("State(")
        for pid, p in self.placements.items():
            print(f"  {pid}: position={p.position}, orientation={p.orientation}")
        print(")")

    def copy(self):
        return State({
            pid: Placement(
                list(p.position) if p.position is not None else None,
                list(p.orientation),
            )
            for pid, p in self.placements.items()
        })

    # menyimpan dict sebuah state ke dalam bentuk tuple
    def key(self):
        return tuple(
            sorted(
                (
                    pid,
                    tuple(p.position) if p.position is not None else None,
                    tuple(p.orientation),
                )
                for pid, p in self.placements.items()
            )
        )

    def to_dict(self):
        return {
            "placements": {
                pid: {"position": p.position, "orientation": p.orientation}
                for pid, p in self.placements.items()
            }
        }

    def occupancy(self, problem):
        pkgs = problem.package_map
        occ = {}
        for pid, p in self.placements.items():
            if p.position is None:
                continue
            dx, dy, dz = pkgs[pid].effective_dims(p.orientation)
            x, y, z = p.position
            for i in range(x, x + dx):
                for j in range(y, y + dy):
                    for k in range(z, z + dz):
                        occ[(i, j, k)] = pid
        return occ
