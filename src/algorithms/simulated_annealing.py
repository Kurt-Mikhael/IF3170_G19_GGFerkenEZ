import math
import time

from src.algorithms.common import build_result
from src.neighbors import sample_random_neighbor
from src.objective import evaluate


class SimulatedAnnealing:

    def __init__(self, problem, rng):
        self.problem = problem
        self.rng = rng

    def print(self):
        print(f"SimulatedAnnealing(packages={len(self.problem.packages)})")

    def run(
        self,
        initial_state,
        initial_temperature=100.0,
        minimum_temperature=0.1,
        cooling_rate=0.995,
        max_iterations=10_000,
    ):
        t0 = time.perf_counter()

        start = initial_state.copy()
        current = initial_state.copy()
        current_value = evaluate(self.problem, current)
        evals = 1
        best = current.copy()
        best_value = current_value
        temperature = initial_temperature
        iteration = 0
        accepted = 0
        bad_accepted = 0
        bad_rejected = 0
        stuck_count = 0

        history = [
            {
                "iteration": 0,
                "temperature": temperature,
                "current_value": current_value,
                "best_value": best_value,
                "acceptance_probability": None,
            }
        ]

        stop_reason = "max_iterations"

        # reference to materi kuliah AI BeyondClassicalSearch, tp jika ada yg diluar itu maka akan ditulis secara explicit
        while iteration < max_iterations and temperature >= minimum_temperature:
            neighbour = sample_random_neighbor(self.problem, current, self.rng)
            evals += 1

            if neighbour is None:
                stop_reason = "no_valid_neighbors"
                break

            neighbour_value = evaluate(self.problem, neighbour)
            evals += 1
            delta = neighbour_value - current_value

            if delta > 0:
                # gerakan lebih baik selalu diterima (reference to materi kuliah AI BeyondClassicalSearch)
                acceptance_prob = 1.0
                current = neighbour
                current_value = neighbour_value
                accepted += 1

                if current_value > best_value:
                    best = current.copy()
                    best_value = current_value
            else:
                # gerakan sama atau lebih buruk bisa diterima dengan probabilitas (reference to materi kuliah AI BeyondClassicalSearch)
                acceptance_prob = math.exp(delta / temperature)

                # aturan penerimaan acak (Metropolis acceptance rule utk SA)
                # reference: S. Kirkpatrick, C. D. Gelatt, Jr., dan M. P. Vecchi, "Optimization by Simulated Annealing", Science, 1983. https://doi.org/10.1126/science.220.4598.671
                if self.rng.random() < acceptance_prob:
                    current = neighbour
                    current_value = neighbour_value
                    accepted += 1
                    bad_accepted += 1
                else:
                    bad_rejected += 1
                    stuck_count += 1

            iteration += 1
            history.append(
                {
                    "iteration": iteration,
                    "temperature": round(temperature, 6),
                    "current_value": current_value,
                    "best_value": best_value,
                    "acceptance_probability": round(acceptance_prob, 6),
                }
            )
            temperature *= cooling_rate

        if stop_reason == "max_iterations" and temperature < minimum_temperature:
            stop_reason = "temperature_minimum_reached"

        params = {
            "initial_temperature": initial_temperature,
            "minimum_temperature": minimum_temperature,
            "cooling_rate": cooling_rate,
            "max_iterations": max_iterations,
        }
        extra = {
            **params,
            "stuck_count": stuck_count,
            "bad_accepted": bad_accepted,
            "bad_rejected": bad_rejected,
        }

        return build_result(
            "simulated_annealing",
            params,
            start,
            history[0]["current_value"],
            best,
            best_value,
            iteration,
            accepted,
            evals,
            time.perf_counter() - t0,
            stop_reason,
            history,
            extra,
        )