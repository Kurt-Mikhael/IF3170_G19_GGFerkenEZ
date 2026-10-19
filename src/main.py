import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms.genetic_algorithm import GeneticAlgorithm
from src.algorithms.hill_climb import HillClimb  
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.initialization import generate_initial_state 
from src.reader import load_problem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--algorithm", choices=["steepest_ascent", "sideways", "stochastic", "random_restart", "simulated_annealing", "genetic_algorithm", "all",], default="all")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-sideways", type=int, default=10)
    ap.add_argument("--max-restart", type=int, default=3)
    ap.add_argument("--max-iterations", type=int, default=10_000, help="Batas iterasi Stochastic Hill Climbing")
    ap.add_argument("--sa-initial-temperature", type=float, default=100.0, help="Suhu awal SA")
    ap.add_argument("--sa-minimum-temperature", type=float, default=0.1, help="Suhu minimum SA")
    ap.add_argument("--sa-cooling-rate", type=float, default=0.995, help="Faktor pendinginan SA")
    ap.add_argument("--sa-max-iterations", type=int, default=10_000, help="Batas iterasi maksimum SA")
    ap.add_argument("--sa-stuck-patience", type=int, default=100, help="Jumlah proposal berturut-turut tanpa perbaikan agar SA dianggap stuck")
    ap.add_argument("--ga-population-size", type=int, default=50, help="Jumlah individu GA (minimal 2)")
    ap.add_argument("--ga-iterations", type=int, default=100, help="Jumlah generasi GA (minimal 1)")
    ap.add_argument("--ga-experiment", action="store_true", help="Jalankan dua rangkaian eksperimen GA: populasi tetap dengan variasi iterasi, dan iterasi tetap dengan variasi populasi")
    ap.add_argument("--ga-iteration-variants", type=int, nargs=3, default=[50, 100, 200], help="Tiga variasi jumlah iterasi (populasi tetap = --ga-population-size)")
    ap.add_argument("--ga-population-variants", type=int, nargs=3, default=[20, 50, 100], help="Tiga variasi jumlah populasi (iterasi tetap = --ga-iterations)")
    ap.add_argument("--output-dir", default="output", help="Hasil disimpan di <output-dir>/<nama tc>/")
    args = ap.parse_args()
    if args.algorithm in {"genetic_algorithm", "all"}:
        if min([args.ga_population_size] + args.ga_population_variants) < 2:
            ap.error("jumlah populasi GA harus minimal 2")
        if min([args.ga_iterations] + args.ga_iteration_variants) < 1:
            ap.error("jumlah iterasi GA harus minimal 1")

    problem = load_problem(args.input)
    algos = (
        ["steepest_ascent", "sideways", "random_restart", "simulated_annealing", "genetic_algorithm", "stochastic"]
        if args.algorithm == "all"
        else [args.algorithm]
    )
    tc_name = os.path.splitext(os.path.basename(args.input))[0]
    out_dir = os.path.join(args.output_dir, tc_name)
    os.makedirs(out_dir, exist_ok=True)

    # setiap job adalah tuple dari (algoritma, konfigurasi GA, nama rangkaian eksperimen)
    jobs = []
    for algo in algos:
        if algo != "genetic_algorithm":
            jobs.append((algo, None, None))
        elif args.ga_experiment:
            # konfigurasi yang muncul di kedua rangkaian cukup dijalankan sekali
            configs = {}
            for it in args.ga_iteration_variants:
                configs.setdefault((args.ga_population_size, it), []).append("vary_iterations")
            for pop in args.ga_population_variants:
                configs.setdefault((pop, args.ga_iterations), []).append("vary_population")
            jobs.extend((algo, config, series) for config, series in configs.items())
        else:
            jobs.append((algo, (args.ga_population_size, args.ga_iterations), []))

    for algo, ga_config, series in jobs:
        for run in range(1, args.runs + 1):
            seed = args.seed + run - 1
            rng = random.Random(seed)
            t0 = time.perf_counter()
            if algo != "genetic_algorithm":
                init = generate_initial_state(problem, rng)

            if algo == "genetic_algorithm":
                ga = GeneticAlgorithm(problem, rng)
                result = ga.genetic_algorithm(
                    population_size=ga_config[0],
                    iterations=ga_config[1],
                )
            elif algo == "simulated_annealing":
                sa = SimulatedAnnealing(problem, rng)
                result = sa.run(init, initial_temperature=args.sa_initial_temperature, minimum_temperature=args.sa_minimum_temperature, cooling_rate=args.sa_cooling_rate, max_iterations=args.sa_max_iterations, stuck_patience=args.sa_stuck_patience)
            else:
                hc = HillClimb(problem, rng)
                if algo == "steepest_ascent":
                    result = hc.steepest_ascent(init)
                elif algo == "sideways":
                    result = hc.sideways(init, args.max_sideways)
                elif algo == "stochastic":
                    result = hc.stochastic(init, args.max_iterations)
                else:
                    result = hc.random_restart(init, args.max_restart)
            # duration_seconds = durasi algoritma aja 
            result["total_duration_seconds"] = time.perf_counter() - t0
            result["run_id"], result["seed"], result["input"] = run, seed, tc_name
            name = algo
            if ga_config is not None:
                result["experiment_series"] = series
                name += f"_pop{ga_config[0]}_it{ga_config[1]}"
            path = os.path.join(out_dir, f"{name}_run{run}_seed{seed}.json")
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(
                f"{name} run {run}: {result['initial_value']} -> {result['final_value']} "
                f"({result['iterations']} it, {result['duration_seconds']:.2f}s, {result['stop_reason']})"
            )


if __name__ == "__main__":
    main()
