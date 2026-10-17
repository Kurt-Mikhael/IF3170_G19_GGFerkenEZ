from src.constraints import validate_state
from src.neighbors import candidate_positions
from src.package import ORIENTATIONS
from src.placement import Placement
from src.state import State


def generate_initial_state(problem, rng):
    pkgs = problem.package_map
    state = State(
        {pid: Placement(None, ["x", "y", "z"]) for pid in pkgs}
    )
    order = list(pkgs)
    rng.shuffle(order)
    for pid in order:
        oris = list(ORIENTATIONS)
        rng.shuffle(oris)
        placed = False
        for ori in oris:
            positions = list(candidate_positions(problem, pkgs[pid], ori))
            rng.shuffle(positions)
            for pos in positions:
                cand = state.copy()
                cand.placements[pid] = Placement(pos, list(ori))
                valid, _ = validate_state(problem, cand)
                if valid:
                    state = cand
                    placed = True
                    break
            if placed:
                break
    return state
