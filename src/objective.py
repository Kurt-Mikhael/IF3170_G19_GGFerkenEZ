def evaluate(problem, state):
    values = {p.id: p.value for p in problem.packages}
    return sum(
        values[pid] for pid, p in state.placements.items() if p.position is not None
    )
