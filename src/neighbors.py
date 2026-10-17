from src.constraints import validate_state


def candidate_positions(problem, package, orientation):
    truck = problem.truck
    dx, dy, dz = package.effective_dims(orientation)
    W, L, H = truck.w, truck.l, truck.h
    if dx > W or dy > L or dz > H:
        return
    for x in range(W - dx + 1):
        for y in range(L - dy + 1):
            for z in range(H - dz + 1):
                yield [x, y, z]


def is_new_valid(problem, cand, seen):
    key = cand.key()
    if key in seen:
        return False
    seen.add(key)
    valid, _ = validate_state(problem, cand)
    return valid


def iter_valid_neighbors(problem, state):
    pkgs = problem.package_map
    ids = list(state.placements)
    seen = {state.key()}

    # Move: pindahkan satu paket ke koordinat lain, orientasi tetap
    for pid in ids:
        cur = state.placements[pid]
        for pos in candidate_positions(problem, pkgs[pid], cur.orientation):
            cand = state.copy()
            cand.placements[pid].position = pos
            if is_new_valid(problem, cand, seen):
                yield cand

    # Rotate: rotasi satu paket 90° terhadap sumbu x, y, atau z, posisi tetap
    for pid in ids:
        for axis in ("x", "y", "z"):
            cand = state.copy()
            cand.placements[pid].rotate(axis)
            if is_new_valid(problem, cand, seen):
                yield cand

    # Swap: tukar posisi dua paket, di dalam maupun di luar truk
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]
            pi, pj = state.placements[i].position, state.placements[j].position
            if pi is None and pj is None:
                continue
            cand = state.copy()
            cand.placements[i].position = list(pj) if pj is not None else None
            cand.placements[j].position = list(pi) if pi is not None else None
            if is_new_valid(problem, cand, seen):
                yield cand
