import random
import time

from src.algorithms.common import build_result
from src.constraints import validate_state
from src.objective import evaluate
from src.package import ORIENTATIONS
from src.placement import Placement
from src.state import State


class GeneticAlgorithm:
    CROSSOVER_PROBABILITY = 0.80
    MUTATION_PROBABILITY = 0.30
    REPAIR_ATTEMPTS = 20
    MUTATION_ATTEMPTS = 10

    def __init__(self, problem, rng):
        self.problem = problem
        self.rng = rng
        self.packages = problem.package_map

    def random_inside_position(self, package, orientation, rng=None, heights=None):
        rng = self.rng if rng is None else rng
        dx, dy, dz = package.effective_dims(orientation)
        limits = (self.problem.truck.w - dx, self.problem.truck.l - dy,self.problem.truck.h - dz)

        if min(limits) < 0:
            return None

        if heights is None:
            z = rng.randint(0, limits[2])
        else:
            allowed = [height for height in heights if 0 <= height <= limits[2]]
            if not allowed:
                return None
            z = rng.choice(allowed)

        return [rng.randint(0, limits[0]), rng.randint(0, limits[1]), z]

    def select_parents(self, population, fitness_scores):
        if any(score < 0 for score in fitness_scores):
            raise ValueError("Fitness scores must be nonnegative.")

        weights = fitness_scores if sum(fitness_scores) else None
        return tuple(self.rng.choices(population, weights=weights, k=2))

    def _empty_state(self):
        return State({
            pid: Placement(None, ["x", "y", "z"])
            for pid in self.packages
        })

    def _can_insert(self, pid, position, orientation, inside):
        package = self.packages[pid]
        truck = self.problem.truck
        x, y, z = position
        dx, dy, dz = package.effective_dims(orientation)

        if not (0 <= x <= truck.w - dx and 0 <= y <= truck.l - dy and 0 <= z <= truck.h - dz):
            return False

        supported = z == 0
        for other_id, (ox, oy, oz, odx, ody, odz) in inside.items():
            if not (x < ox + odx and ox < x + dx and y < oy + ody and oy < y + dy):
                continue

            if z < oz + odz and oz < z + dz:
                return False
            if self.packages[other_id].is_fragile and z >= oz + odz:
                return False
            if package.is_fragile and oz >= z + dz:
                return False
            if oz + odz == z and not self.packages[other_id].is_fragile:
                supported = True

        return supported

    def _insert(self, state, pid, orientation, inside, loaded_weight, rng, preferred=None):
        package = self.packages[pid]
        if loaded_weight + package.weight > self.problem.truck.max_capacity:
            return False

        heights = sorted({0} | {box[2] + box[5]
                for other_id, box in inside.items()
                if not self.packages[other_id].is_fragile
            }
        )
        attempts = self.REPAIR_ATTEMPTS + (preferred is not None)

        for attempt in range(attempts):
            if attempt == 0 and preferred is not None:
                position = list(preferred)
            else:
                position = self.random_inside_position(package, orientation, rng=rng, heights=heights)

            if position is None:
                return False

            if self._can_insert(pid, position, orientation, inside):
                state.placements[pid] = Placement(position, list(orientation))
                inside[pid] = (*position, *package.effective_dims(orientation))
                return True

        return False

    def _generate_initial_state(self, rng):
        state = self._empty_state()
        inside, loaded_weight = {}, 0
        ids = list(self.packages)
        rng.shuffle(ids)

        for pid in ids:
            orientations = list({
                self.packages[pid].effective_dims(orientation): orientation
                for orientation in ORIENTATIONS
            }.values())
            rng.shuffle(orientations)
            for orientation in orientations:
                if self._insert(state, pid, orientation, inside, loaded_weight, rng):
                    loaded_weight += self.packages[pid].weight
                    break

        return state

    def crossover(self, parent_a, parent_b):
        inherited = {
            pid: self.rng.choice((parent_a, parent_b)).placements[pid]
            for pid in self.packages
        }
        child = State({
            pid: Placement(None, list(gene.orientation))
            for pid, gene in inherited.items()
        })
        ids = [pid for pid, gene in inherited.items() if gene.position is not None]
        self.rng.shuffle(ids)
        ids.sort(key=lambda pid: inherited[pid].position[2])
        inside, loaded_weight = {}, 0

        for pid in ids:
            gene = inherited[pid]
            if self._insert(
                child, pid, gene.orientation, inside, loaded_weight,
                self.rng, preferred=gene.position,
            ):
                loaded_weight += self.packages[pid].weight

        return child

    def mutate(self, state):
        ids = list(state.placements)
        if not ids:
            return state.copy()

        operation = self.rng.choice(("swap", "move", "rotate"))
        original_key = state.key()

        for _ in range(self.MUTATION_ATTEMPTS):
            candidate = state.copy()

            if operation == "swap":
                if len(ids) < 2:
                    break
                first_id, second_id = self.rng.sample(ids, 2)
                first = candidate.placements[first_id]
                second = candidate.placements[second_id]
                first.position, second.position = second.position, first.position

            elif operation == "move":
                pid = self.rng.choice(ids)
                placement = candidate.placements[pid]
                if self.rng.random() < 0.20:
                    placement.position = None
                else:
                    position = self.random_inside_position(
                        self.packages[pid], placement.orientation
                    )
                    if position is None:
                        continue
                    placement.position = position

            else:
                pid = self.rng.choice(ids)
                placement = candidate.placements[pid]
                before = self.packages[pid].effective_dims(placement.orientation)
                axis = self.rng.choice(("x", "y", "z"))
                placement.rotate(axis)
                if self.packages[pid].effective_dims(placement.orientation) == before:
                    continue

            if candidate.key() == original_key:
                continue

            valid, _ = validate_state(self.problem, candidate)
            if valid:
                return candidate

        return state.copy()

    @staticmethod
    def _statistics(iteration, scores, best_value):
        return {
            "iteration": iteration,
            "population_max": max(scores),
            "population_mean": sum(scores) / len(scores),
            "best_so_far": best_value,
        }

    def genetic_algorithm(self, population_size=50, iterations=100):
        if population_size < 2:
            raise ValueError("Population size must be at least 2.")
        if iterations < 1:
            raise ValueError("Iterations must be positive.")

        started = time.perf_counter()
        initialization_rng = random.Random(self.rng.getrandbits(128))
        population = [
            self._generate_initial_state(initialization_rng)
            for _ in range(population_size)
        ]
        initial_population = population
        scores = [evaluate(self.problem, state) for state in population]
        best_index = max(range(population_size), key=scores.__getitem__)
        best_state = population[best_index].copy()
        best_value = scores[best_index]
        initial_state, initial_value = best_state.copy(), best_value
        history = [self._statistics(0, scores, best_value)]
        best_generation = crossovers = mutations = accepted_mutations = 0

        for generation in range(1, iterations + 1):
            next_population = []

            while len(next_population) < population_size:
                parent_a, parent_b = self.select_parents(population, scores)

                if self.rng.random() < self.CROSSOVER_PROBABILITY:
                    child = self.crossover(parent_a, parent_b)
                    crossovers += 1
                else:
                    child = self.rng.choice((parent_a, parent_b)).copy()

                if self.rng.random() < self.MUTATION_PROBABILITY:
                    mutations += 1
                    before = child.key()
                    child = self.mutate(child)
                    accepted_mutations += child.key() != before

                next_population.append(child)

            population = next_population
            scores = [evaluate(self.problem, state) for state in population]
            best_index = max(range(population_size), key=scores.__getitem__)

            if scores[best_index] > best_value:
                best_state = population[best_index].copy()
                best_value = scores[best_index]
                best_generation = generation

            history.append(self._statistics(generation, scores, best_value))

        duration = time.perf_counter() - started

        return build_result(
            algorithm="genetic_algorithm",
            parameters={"population_size": population_size, "iterations": iterations},
            initial_state=initial_state,
            initial_value=initial_value,
            final_state=best_state,
            final_value=best_value,
            iterations=iterations,
            accepted_moves=accepted_mutations,
            objective_evaluations=population_size * (iterations + 1),
            duration_seconds=duration,
            stop_reason="iteration_limit_reached",
            history=history,
            extra={
                "initial_state_selection": "best_individual_in_initial_population",
                "initial_population": [state.to_dict() for state in initial_population],
                "final_population_fitness": scores,
                "best_generation": best_generation,
                "crossovers": crossovers,
                "mutation_calls": mutations,
                "accepted_mutations": accepted_mutations,
                "settings": {
                    "selection": "roulette_wheel_with_replacement",
                    "crossover_probability": self.CROSSOVER_PROBABILITY,
                    "mutation_probability": self.MUTATION_PROBABILITY,
                    "elitism": False,
                    "repair_attempts": self.REPAIR_ATTEMPTS,
                    "mutation_attempts": self.MUTATION_ATTEMPTS,
                },
            },
        )
