import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


ALGORITHM_NAMES = {
    "steepest_ascent": "Steepest-Ascent Hill Climbing",
    "sideways": "Hill Climbing dengan Sideways",
    "random_restart": "Random-Restart Hill Climbing",
    "simulated_annealing": "Simulated Annealing",
    "genetic_algorithm": "Genetic Algorithm",
}


def algorithm_view(result):
    algorithm = result["algorithm"]
    history = pd.DataFrame(result["history"])
    extra = result.get("extra", {})
    title = ALGORITHM_NAMES.get(algorithm, algorithm)

    if algorithm in {"steepest_ascent", "sideways"}:
        if algorithm == "sideways":
            title += f" | Sideways diterima: {extra['sideways_moves']}"

        fig = px.line(
            history,
            x="iteration",
            y="current_value",
            markers=True,
            title=title,
            labels={"iteration": "Iterasi", "current_value": "Nilai state"},
        )
        last = history.iloc[-1]
        fig.add_annotation(
            x=last["iteration"],
            y=last["current_value"],
            text=f"Berhenti: {result['stop_reason']}",
            showarrow=True,
            ax=0,
            ay=-40,
        )

    elif algorithm == "random_restart":
        fig = go.Figure()
        for search_id, part in history.groupby("search_id"):
            label = f"Pencarian {search_id} ({extra['iterations_per_search'][search_id]} it)"
            if search_id == extra["best_search"]:
                label += " (terbaik)"
            fig.add_scatter(x=part["iteration"], y=part["current_value"], mode="lines+markers", name=label)
        fig.add_scatter(x=history["iteration"], y=history["best_value"], mode="lines",
                        name="Terbaik sepanjang pencarian", line={"dash": "dash"})
        fig.update_layout(
            title=(f"{title} | Restart: {extra['restart_count']} dari maks {extra['maximum_restart']}"
                   f" | Total iterasi: {extra['total_iterations']}"),
            xaxis_title="Iterasi (kumulatif seluruh pencarian)",
            yaxis_title="Nilai state",
        )

    elif algorithm == "simulated_annealing":
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            subplot_titles=("Nilai state", "Suhu", "Probabilitas penerimaan min(1, e^(ΔE/T))"),
        )
        for field, label, row in [
            ("current_value", "Nilai saat ini", 1),
            ("best_value", "Nilai terbaik", 1),
            ("temperature", "Suhu", 2),
            ("acceptance_probability", "Probabilitas", 3),
        ]:
            fig.add_trace(
                go.Scatter(x=history["iteration"], y=history[field], mode="lines", name=label),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="Nilai", row=1, col=1)
        fig.update_yaxes(title_text="Suhu", type="log", row=2, col=1)
        fig.update_yaxes(title_text="Probabilitas", range=[0, 1.05], row=3, col=1)
        fig.update_xaxes(title_text="Iterasi", row=3, col=1)
        fig.update_layout(title=f"{title} | Stuck di local optima: {extra.get('stuck_count', 0)} kali", height=750)

    elif algorithm == "genetic_algorithm":
        fig = go.Figure()
        for field, label in [
            ("population_max", "Maksimum populasi"),
            ("population_mean", "Rata-rata populasi"),
            ("best_so_far", "Terbaik sepanjang pencarian"),
        ]:
            fig.add_scatter(x=history["iteration"], y=history[field], mode="lines", name=label)
        fig.update_layout(title=title, xaxis_title="Generasi", yaxis_title="Fitness")

    else:
        raise ValueError(f"Algoritma belum dikenali: {algorithm}")

    return fig


def experiment_view(results):
    records = []
    for result in results:
        extra = result.get("extra", {})
        records.append({
            "algorithm": result["algorithm"],
            "parameters": json.dumps(result["parameters"], sort_keys=True, ensure_ascii=False),
            "seed": result.get("seed"),
            "run_id": result.get("run_id"),
            "initial_value": result["initial_value"],
            "final_value": result["final_value"],
            "gain": result["final_value"] - result["initial_value"],
            "seconds": result["duration_seconds"],
            "iterations": extra.get("total_iterations", result["iterations"]),
            "stop_reason": result["stop_reason"],
        })

    if not records:
        raise ValueError("Belum ada hasil eksperimen.")

    data = pd.DataFrame(records)
    summary = (
        data.groupby(["algorithm", "parameters"], dropna=False)
        .agg(
            runs=("final_value", "size"),
            mean_value=("final_value", "mean"),
            std_value=("final_value", "std"),
            min_value=("final_value", "min"),
            max_value=("final_value", "max"),
            mean_seconds=("seconds", "mean"),
        )
        .reset_index()
    )
    labels = {
        "algorithm": "Algoritma",
        "parameters": "Parameter",
        "final_value": "Nilai akhir",
        "initial_value": "Nilai awal",
        "seconds": "Durasi (detik)",
        "iterations": "Iterasi/generasi (total untuk random restart)",
        "seed": "Seed",
        "run_id": "Run",
        "stop_reason": "Alasan berhenti",
    }
    scores = px.box(
        data,
        x="algorithm",
        y="final_value",
        color="parameters",
        points="all",
        hover_data=["seed", "run_id", "initial_value"],
        title="Distribusi nilai akhir antar-run",
        labels=labels,
    )
    timing = px.scatter(
        data,
        x="seconds",
        y="final_value",
        color="algorithm",
        hover_data=["parameters", "seed", "run_id", "iterations", "stop_reason"],
        title="Durasi pencarian terhadap nilai akhir",
        labels=labels,
    )
    return data, summary, scores, timing
