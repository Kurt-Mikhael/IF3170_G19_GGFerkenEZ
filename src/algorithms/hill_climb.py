import time

from src.algorithms.common import build_result
from src.neighbors import iter_valid_neighbors, sample_random_neighbor
from src.objective import evaluate


class HillClimb:
    def __init__(self, problem, rng):
        self.problem = problem
        self.rng = rng

    def print(self):
        print(f"HillClimb(packages={len(self.problem.packages)})")

    def steepest_ascent(self, initial_state):
        t0 = time.perf_counter()
        start = initial_state.copy()
        current = initial_state.copy()
        current_value = evaluate(self.problem, current)
        evals = 1
        history = [{"iteration": 0, "current_value": current_value, "best_value": current_value}]
        accepted = 0
        iteration = 0

        while True:
            best_value, best_list = current_value, []
            for cand in iter_valid_neighbors(self.problem, current):
                v = evaluate(self.problem, cand)
                evals += 1
                if v > best_value:
                    best_value, best_list = v, [cand]
                elif v == best_value:
                    best_list.append(cand)
            if best_value > current_value:
                current = self.rng.choice(best_list) if len(best_list) > 1 else best_list[0]
                current_value = best_value
                accepted += 1
                iteration += 1
                history.append(
                    {"iteration": iteration, "current_value": current_value, "best_value": current_value}
                )
            else:
                iteration += 1
                history.append(
                    {"iteration": iteration, "current_value": current_value, "best_value": current_value}
                )
                stop = "no_valid_neighbors" if not best_list else "no_improving_neighbor"
                break

        return build_result(
            "steepest_ascent", {}, start, history[0]["current_value"],
            current, current_value, iteration, accepted, evals,
            time.perf_counter() - t0, stop, history, {},
        )

    def sideways(self, initial_state, max_sideways=10):
        t0 = time.perf_counter()
        start = initial_state.copy()
        current = initial_state.copy()
        current_value = evaluate(self.problem, current)
        evals = 1
        history = [{"iteration": 0, "current_value": current_value, "best_value": current_value}]
        accepted = sideways = iteration = 0

        while True:
            best_value, best_list = current_value, []
            for cand in iter_valid_neighbors(self.problem, current):
                v = evaluate(self.problem, cand)
                evals += 1
                if v > best_value:
                    best_value, best_list = v, [cand]
                elif v == best_value:
                    best_list.append(cand)
            if best_value > current_value:
                move, sideways_move = True, False
            elif best_list and sideways < max_sideways:
                move, sideways_move = True, True
            else:
                move = False
            iteration += 1
            if not move:
                history.append(
                    {"iteration": iteration, "current_value": current_value, "best_value": current_value}
                )
                if not best_list:
                    stop = "no_valid_neighbors"
                elif sideways >= max_sideways:
                    stop = "sideways_limit_reached"
                else:
                    stop = "no_improving_neighbor"
                break
            current = self.rng.choice(best_list) if len(best_list) > 1 else best_list[0]
            current_value = best_value
            accepted += 1
            sideways += sideways_move
            history.append(
                {"iteration": iteration, "current_value": current_value, "best_value": current_value}
            )

        return build_result(
            "sideways", {"maximum_sideways_move": max_sideways},
            start, history[0]["current_value"], current, current_value,
            iteration, accepted, evals, time.perf_counter() - t0, stop, history,
            {"maximum_sideways_move": max_sideways, "sideways_moves": sideways},
        )

    def random_restart(self, initial_state, max_restart=3):
        from src.initialization import generate_initial_state

        t0 = time.perf_counter()
        starts = [initial_state.copy()] + [
            generate_initial_state(self.problem, self.rng) for _ in range(max_restart)
        ]
        runs = [self.__class__(self.problem, self.rng).steepest_ascent(s) for s in starts]
        best_idx = max(range(len(runs)), key=lambda i: runs[i]["final_value"])
        best = runs[best_idx]
        searches = [
            {
                "search_id": i,
                "initial_state": starts[i].to_dict(),
                "final_state": r["final_state"],
                "initial_value": r["initial_value"],
                "final_value": r["final_value"],
                "iterations": r["iterations"],
                "accepted_moves": r["accepted_moves"],
            }
            for i, r in enumerate(runs)
        ]
        return build_result(
            "random_restart", {"maximum_restart": max_restart},
            starts[0].copy(), runs[0]["initial_value"],
            best["final_state"], best["final_value"],
            best["iterations"], best["accepted_moves"],
            sum(r["objective_evaluations"] for r in runs),
            time.perf_counter() - t0, best["stop_reason"], best["history"],
            {
                "maximum_restart": max_restart,
                "num_searches": len(runs),
                "best_search": best_idx,
                "total_iterations": sum(r["iterations"] for r in runs),
                "restarts": searches,
            },
        )

    def stochastic(self, initial_state, max_iterations=10_000):
        # ambil satu  neighbour acak, pindah hanya jika lebih baik dari state saat ini
        # referensi: materi kuliah AI BeyondClassicalSearch bagian Stochastic Hill-climbing
        t0 = time.perf_counter()
        start = initial_state.copy()
        current = initial_state.copy()
        current_value = evaluate(self.problem, current)
        evals = 1
        best = current.copy()
        best_value = current_value
        accepted = iteration = 0
        history = [
            {"iteration": 0, "current_value": current_value, "best_value": best_value, "accepted": False}
        ]
        stop = "max_iterations"

        while iteration < max_iterations:
            neighbour = sample_random_neighbor(self.problem, current, self.rng)
            if neighbour is None:
                stop = "no_valid_neighbors"
                break

            neighbour_value = evaluate(self.problem, neighbour)
            evals += 1
            delta = neighbour_value - current_value

            is_accepted = delta > 0
            if is_accepted:
                current = neighbour
                current_value = neighbour_value
                accepted += 1
                if current_value > best_value:
                    best = current.copy()
                    best_value = current_value

            iteration += 1
            history.append(
                {
                    "iteration": iteration,
                    "current_value": current_value,
                    "best_value": best_value,
                    "accepted": is_accepted,
                }
            )

        return build_result(
            "stochastic", {"max_iterations": max_iterations},
            start, history[0]["current_value"], best, best_value,
            iteration, accepted, evals, time.perf_counter() - t0, stop, history,
            {"max_iterations": max_iterations, "rejected_moves": iteration - accepted},
        )