from src.placement import Placement


class State:
    def __init__(self, placements):
        self.placements = placements

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
