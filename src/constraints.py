def overlap_1d(a0, a1, b0, b1):
    return max(a0, b0) < min(a1, b1)


def footprint_overlap(box_a, box_b):
    xa, ya, _, dxa, dya, _ = box_a
    xb, yb, _, dxb, dyb, _ = box_b
    return overlap_1d(xa, xa + dxa, xb, xb + dxb) and overlap_1d(ya, ya + dya, yb, yb + dyb)


def box_overlap(box_a, box_b):
    _, _, za, _, _, dza = box_a
    _, _, zb, _, _, dzb = box_b
    return footprint_overlap(box_a, box_b) and overlap_1d(za, za + dza, zb, zb + dzb)


def collect_boxes(problem, state, pkgs, violations):
    truck = problem.truck
    inside = {}

    for pid, p in state.placements.items():
        if p.position is None:
            continue
        x, y, z = p.position
        dx, dy, dz = pkgs[pid].effective_dims(p.orientation)
        if not (x >= 0 and y >= 0 and z >= 0 and x + dx <= truck.w and y + dy <= truck.l and z + dz <= truck.h):
            violations.append(f"{pid}: menembus dinding")
            continue
        inside[pid] = (x, y, z, dx, dy, dz)

    return inside


def check_overlap(inside, violations):
    ids = list(inside)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]
            if box_overlap(inside[i], inside[j]):
                violations.append(f"{i}/{j}: overlap")


def check_capacity(problem, inside, pkgs, violations):
    totalW = sum(pkgs[pid].weight for pid in inside)
    if totalW > problem.truck.max_capacity:
        violations.append(f"overload {totalW} > {problem.truck.max_capacity}")


def check_floating(inside, pkgs, violations):
    for pid, box in inside.items():
        z = box[2]
        if z == 0:
            continue
        supported = any(
            not pkgs[q].is_fragile
            and other[2] + other[5] == z
            and footprint_overlap(box, other)
            for q, other in inside.items()
            if q != pid
        )
        if not supported:
            violations.append(f"{pid}: melayang")


def check_fragile(inside, pkgs, violations):
    for pid, box in inside.items():
        if not pkgs[pid].is_fragile:
            continue
        top = box[2] + box[5]
        for q, other in inside.items():
            if q == pid:
                continue
            if footprint_overlap(box, other) and other[2] >= top:
                violations.append(f"{pid}: fragile tertindih {q}")
                break


def validate_state(problem, state):
    pkgs = problem.package_map
    violations = []

    inside = collect_boxes(problem, state, pkgs, violations)
    check_overlap(inside, violations)
    check_capacity(problem, inside, pkgs, violations)
    check_floating(inside, pkgs, violations)
    check_fragile(inside, pkgs, violations)

    return (len(violations) == 0, violations)
