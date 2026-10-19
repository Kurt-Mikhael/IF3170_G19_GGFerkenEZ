import time

from src.algorithms.common import build_result
from src.neighbors import iter_valid_neighbors, sample_random_neighbor
from src.objective import evaluate


class HillClimb:
    def __init__(self, problem, rng):
        self.problem = problem
        self.rng = rng

    def steepest_ascent(self, initial_state):
        # referensi: materi kuliah AI BeyondClassicalSearch bagian Stochastic Hill-climbing
        # setiap state menhidupi semua successor dan cari succesor yang menghasilkan state value terbaik. Jika tidak ada successor yang lebih baik, berhenti.
        t0 = time.perf_counter()
        start = initial_state.copy()
        current = initial_state.copy()
        current_value = evaluate(self.problem, current)
        evals = 1
        history = [{"iteration": 0, "current_value": current_value, "best_value": current_value}]
        accepted = 0
        iteration = 0

        while True:
            # cari semua tetangga yang valid, pilih yang terbaik
            best_value, best_list = current_value, []
            for cand in iter_valid_neighbors(self.problem, current):
                v = evaluate(self.problem, cand)
                evals += 1
                if v > best_value:
                    best_value, best_list = v, [cand]
                elif v == best_value:
                    best_list.append(cand)
            # jika ada tetangga yang lebih baik, pindah ke salah satunya. Jika tidak ada, berhenti.
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
        # referensi: materi kuliah AI BeyondClassicalSearch bagian Stochastic Hill-climbing
        # sama seperti steepest ascent, tapi jika ada tetangga yang sama baiknya dengan
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
            # jika ada tetangga yang lebih baik, pindah ke salah satunya. Jika tidak ada, tapi ada tetangga yang sama baiknya dan belum melewati batas sideways, pindah ke salah satunya. Jika tidak ada tetangga yang lebih baik atau sama baiknya, berhenti.
            if best_value > current_value:
                move, sideways_move = True, False
            # jika ada tetangga yang sama baiknya, pindah ke salah satunya, iterasi sideways bertambah 1. 
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
                {"iteration": iteration, "current_value": current_value, "best_value": current_value,
                 "sideways": sideways_move}
            )
            if sideways_move and sideways >= max_sideways:
                stop = "sideways_limit_reached"
                break

        return build_result(
            "sideways", {"maximum_sideways_move": max_sideways},
            start, history[0]["current_value"], current, current_value,
            iteration, accepted, evals, time.perf_counter() - t0, stop, history,
            {"maximum_sideways_move": max_sideways, "sideways_moves": sideways},
        )

    def random_restart(self, initial_state, max_restart=3):
        from src.initialization import generate_initial_state
        # referensi: materi kuliah AI BeyondClassicalSearch bagian Stochastic Hill-climbing
        # jalankan steepest ascent beberapa kali dari initial state yang berbeda, ambil hasil terbaik

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
                "stop_reason": r["stop_reason"],
                "history": r["history"],
            }
            for i, r in enumerate(runs)
        ]

        # gabungin riwayat semua pencarian dalam satu sumbu iterasi global
        history, offset, global_best = [], 0, None
        for i, r in enumerate(runs):
            for h in r["history"]:
                if i > 0 and h["iteration"] == 0:
                    offset += 1
                global_best = h["current_value"] if global_best is None else max(global_best, h["current_value"])
                history.append({
                    "iteration": offset + h["iteration"],
                    "search_id": i,
                    "local_iteration": h["iteration"],
                    "current_value": h["current_value"],
                    "best_value": global_best,
                })
            offset += r["history"][-1]["iteration"]
        total_iterations = sum(r["iterations"] for r in runs)

        return build_result(
            "random_restart", {"maximum_restart": max_restart},
            starts[0].copy(), runs[0]["initial_value"],
            best["final_state"], best["final_value"],
            total_iterations, sum(r["accepted_moves"] for r in runs),
            sum(r["objective_evaluations"] for r in runs),
            time.perf_counter() - t0, best["stop_reason"], history,
            {
                "maximum_restart": max_restart,
                "num_searches": len(runs),
                "restart_count": len(runs) - 1,
                "best_search": best_idx,
                "total_iterations": total_iterations,
                "iterations_per_search": [r["iterations"] for r in runs],
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
