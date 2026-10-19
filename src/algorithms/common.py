def ser(s):
    return s.to_dict() if hasattr(s, "to_dict") else s


def build_result(
    algorithm,
    parameters,
    initial_state,
    initial_value,
    final_state,
    final_value,
    iterations,
    accepted_moves,
    objective_evaluations,
    duration_seconds,
    stop_reason,
    history,
    extra,
):
    return {
        "algorithm": algorithm,
        "parameters": parameters,
        "initial_state": ser(initial_state),
        "final_state": ser(final_state),
        "initial_value": initial_value,
        "final_value": final_value,
        "iterations": iterations,
        "accepted_moves": accepted_moves,
        "objective_evaluations": objective_evaluations,
        "duration_seconds": duration_seconds,
        "stop_reason": stop_reason,
        "history": history,
        "extra": extra,
    }
