import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms.hill_climb import HillClimb  
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.initialization import generate_initial_state 
from src.reader import load_problem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument(
        "--algorithm",
        choices=["steepest_ascent", "sideways", "random_restart", "simulated_annealing", "all",],
        default="all",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-sideways", type=int, default=10)
    ap.add_argument("--max-restart", type=int, default=3)
    ap.add_argument("--sa-initial-temperature", type=float, default=100.0, help="Suhu awal SA")
    ap.add_argument("--sa-minimum-temperature", type=float, default=0.1, help="Suhu minimum SA")
    ap.add_argument("--sa-cooling-rate", type=float, default=0.995, help="Faktor pendinginan SA")
    ap.add_argument("--sa-max-iterations", type=int, default=10_000, help="Batas iterasi maksimum SA")
    ap.add_argument("--output-dir", default="output")
    args = ap.parse_args()

    problem = load_problem(args.input)
    algos = (
        ["steepest_ascent", "sideways", "random_restart", "simulated_annealing"]
        if args.algorithm == "all"
        else [args.algorithm]
    )
    os.makedirs(args.output_dir, exist_ok=True)
    for algo in algos:
        for run in range(1, args.runs + 1):
            seed = args.seed + run - 1
            rng = random.Random(seed)
            init = generate_initial_state(problem, rng)

            if algo == "simulated_annealing":
                sa = SimulatedAnnealing(problem, rng)
                result = sa.run(init, initial_temperature=args.sa_initial_temperature, minimum_temperature=args.sa_minimum_temperature, cooling_rate=args.sa_cooling_rate, max_iterations=args.sa_max_iterations)
            else:
                hc = HillClimb(problem, rng)
                if algo == "steepest_ascent":
                    result = hc.steepest_ascent(init)
                elif algo == "sideways":
                    result = hc.sideways(init, args.max_sideways)
                else:
                    result = hc.random_restart(init, args.max_restart)
            result["run_id"], result["seed"] = run, seed
            path = os.path.join(args.output_dir, f"{algo}_run{run}_seed{seed}.json")
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(
                f"{algo} run {run}: {result['initial_value']} -> {result['final_value']} "
                f"({result['iterations']} it, {result['duration_seconds']:.2f}s, {result['stop_reason']})"
            )


if __name__ == "__main__":
    main()
