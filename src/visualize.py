import argparse
import json
from html import escape
from itertools import product
from math import ceil, sqrt
from pathlib import Path
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots

from src.constraints import validate_state
from src.objective import evaluate
from src.placement import Placement
from src.reader import load_problem
from src.state import State
from src.visualization_charts import ALGORITHM_NAMES, algorithm_view


EDGES = [
    (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
    (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
]
FACES = [
    (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5),
    (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6),
    (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
]
PACKAGE_COLUMNS = [
    "Paket", "Status", "Posisi state", "Orientasi", "Ukuran efektif",
    "Nilai", "Berat", "Fragile", "ETA",
]


def package_colors(problem):
    palette = qualitative.Alphabet
    return {
        pid: palette[index % len(palette)]
        for index, pid in enumerate(problem.package_map)
    }


def read_state(problem, data):
    placements = data["placements"]
    if set(placements) != set(problem.package_map):
        raise ValueError("State harus memetakan seluruh ID paket pada input.")

    for pid, item in placements.items():
        position = item["position"]
        if position is not None and (
            len(position) != 3 or any(type(c) is not int for c in position)
        ):
            raise ValueError(f"{pid}: posisi harus berupa tiga bilangan bulat.")
        orientation = item["orientation"]
        if len(orientation) != 3 or set(orientation) != {"x", "y", "z"}:
            raise ValueError(f"{pid}: orientasi harus berupa permutasi x, y, z.")

    state = State({
        pid: Placement(
            list(item["position"]) if item["position"] is not None else None,
            list(item["orientation"]),
        )
        for pid, item in placements.items()
    })
    valid, violations = validate_state(problem, state)
    if not valid:
        raise ValueError("State tidak valid: " + "; ".join(violations))
    return state


def box_vertices(position, dimensions):
    return [
        tuple(p + bit * size for p, bit, size in zip(position, corner, dimensions))
        for corner in product((0, 1), repeat=3)
    ]


def box_mesh(position, dimensions, color, info):
    x, y, z = zip(*box_vertices(position, dimensions))
    i, j, k = zip(*FACES)
    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=0.85, flatshading=True,
        text=info, hoverinfo="text", showlegend=False,
    )


def truck_frame(dimensions):
    vertices = box_vertices((0, 0, 0), dimensions)
    points = []
    for a, b in EDGES:
        points.extend([vertices[a], vertices[b], (None, None, None)])
    x, y, z = zip(*points)
    return go.Scatter3d(
        x=x, y=y, z=z, mode="lines",
        line=dict(color="#334155", width=5),
        hoverinfo="skip", showlegend=False,
    )


def state_view(problem, data, title):
    state = read_state(problem, data)
    truck = problem.truck
    dimensions = (truck.w, truck.l, truck.h)
    if any(type(size) is not int or size <= 0 for size in dimensions):
        raise ValueError("Ukuran peti harus berupa bilangan bulat positif.")

    colors = package_colors(problem)
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "scene"}, {"type": "scene"}]],
        subplot_titles=("Di dalam peti", "Di luar peti (posisi ilustrasi)"),
    )
    fig.add_trace(truck_frame(dimensions), row=1, col=1)

    columns = max(1, ceil(sqrt(len(problem.packages))))
    spacing = 1 + max(
        (max(p.w, p.l, p.h) for p in problem.packages), default=1
    )
    rows = []
    loaded_weight = inside_count = 0

    for index, (pid, package) in enumerate(problem.package_map.items()):
        placement = state.placements[pid]
        size = package.effective_dims(placement.orientation)
        inside = placement.position is not None
        position = placement.position if inside else (
            truck.w + 2 + (index % columns) * spacing,
            (index // columns) * spacing,
            0,
        )
        record = {
            "Paket": pid,
            "Status": "Dalam" if inside else "Luar",
            "Posisi state": str(placement.position),
            "Orientasi": str(placement.orientation),
            "Ukuran efektif": str(size),
            "Nilai": package.value,
            "Berat": package.weight,
            "Fragile": package.is_fragile,
            "ETA": package.eta,
        }
        rows.append(record)
        info = "<br>".join(f"{key}: {escape(str(value))}" for key, value in record.items())
        fig.add_trace(
            box_mesh(position, size, colors[pid], info),
            row=1, col=1 if inside else 2,
        )
        if inside:
            inside_count += 1
            loaded_weight += package.weight

    occupied = {}
    for pid, placement in state.placements.items():
        if placement.position is None:
            continue
        size = problem.package_map[pid].effective_dims(placement.orientation)
        cells = product(*[
            range(start, start + length)
            for start, length in zip(placement.position, size)
        ])
        occupied.update((cell, pid) for cell in cells)
    grid = {
        cell: occupied.get(cell)
        for cell in product(range(truck.w), range(truck.l), range(truck.h))
    }
    utilization = len(occupied) / len(grid)
    outside_rows = max(1, ceil(len(problem.packages) / columns))
    fig.update_scenes(
        aspectmode="data", xaxis_title="x", yaxis_title="y", zaxis_title="z",
        camera=dict(eye=dict(x=1.7, y=1.7, z=1.3)),
    )
    fig.update_layout(
        height=550,
        title=(
            f"{escape(title)} | Nilai={evaluate(problem, state)} | Valid<br>"
            f"Masuk={inside_count}, luar={len(rows) - inside_count} | "
            f"Volume={utilization:.1%} | Berat={loaded_weight}/{truck.max_capacity}"
        ),
        scene=dict(
            xaxis=dict(range=[0, truck.w]),
            yaxis=dict(range=[0, truck.l]),
            zaxis=dict(range=[0, truck.h]),
        ),
        scene2=dict(
            xaxis=dict(range=[truck.w + 1, truck.w + 2 + columns * spacing]),
            yaxis=dict(range=[-1, outside_rows * spacing]),
            zaxis=dict(range=[0, spacing]),
        ),
    )
    return fig, pd.DataFrame(rows, columns=PACKAGE_COLUMNS), grid


def grid_view(problem, grid, title):
    truck = problem.truck
    colors = package_colors(problem)
    ids = [None, *problem.package_map]
    codes = {pid: index for index, pid in enumerate(ids)}
    palette = ["#e5e7eb", *[colors[pid] for pid in ids[1:]]]
    scale = [
        (boundary, color)
        for index, color in enumerate(palette)
        for boundary in (index / len(palette), (index + 1) / len(palette))
    ]
    fig = go.Figure()
    for level in range(truck.h):
        occupants = [
            [grid[(x, y, level)] for x in range(truck.w)]
            for y in range(truck.l)
        ]
        fig.add_trace(go.Heatmap(
            x=list(range(truck.w)), y=list(range(truck.l)),
            z=[[codes[pid] for pid in row] for row in occupants],
            customdata=[
                ["Kosong" if pid is None else escape(str(pid)) for pid in row]
                for row in occupants
            ],
            colorscale=scale, zmin=-0.5, zmax=len(ids) - 0.5,
            showscale=False, visible=(level == 0), xgap=1, ygap=1,
            hovertemplate=(
                "x=%{x}, y=%{y}, z=" + str(level)
                + "<br>Isi=%{customdata}<extra></extra>"
            ),
        ))
    fig.update_layout(
        title=escape(title), height=500,
        xaxis_title="x (indeks sel)", yaxis_title="y (indeks sel)",
        sliders=[dict(
            currentvalue=dict(prefix="Lapisan z = "),
            steps=[dict(
                label=str(level), method="update",
                args=[{"visible": [i == level for i in range(truck.h)]}],
            ) for level in range(truck.h)],
        )],
    )
    fig.update_xaxes(range=[-0.5, truck.w - 0.5], constrain="domain", dtick=1)
    fig.update_yaxes(
        range=[-0.5, truck.l - 0.5], constrain="domain", dtick=1,
        scaleanchor="x", scaleratio=1,
    )
    return fig


def figure_html(figure, filename="grafik"):
    plot_id = f"plot-{uuid4().hex}"
    chart = figure.to_html(
        full_html=False, include_plotlyjs=False,
        div_id=plot_id,
        config={
            "responsive": True,
            "displaylogo": False,
            "displayModeBar": True,
            "toImageButtonOptions": {
                "format": "png", "filename": filename,
                "width": None, "height": None, "scale": 2,
            },
        },
    )
    return (
        '<div class="figure">'
        '<div class="figure-actions">'
        f'<button type="button" data-plot="{plot_id}" '
        f'data-filename="{escape(filename, quote=True)}" '
        'onclick="downloadFigure(this)">Unduh PNG (2x)</button>'
        '<span class="download-status" role="status" aria-live="polite"></span>'
        '</div>' + chart + '</div>'
    )


def table_html(data):
    return '<div class="table">' + data.to_html(index=False, border=0) + "</div>"


def write_page(path, title, content):
    download_script = """
async function downloadFigure(button) {
    const graph = document.getElementById(button.dataset.plot);
    const status = button.parentElement.querySelector('.download-status');
    button.disabled = true;
    status.textContent = 'Menyiapkan gambar...';
    try {
        const size = graph.getBoundingClientRect();
        await Plotly.downloadImage(graph, {
            format: 'png', filename: button.dataset.filename,
            width: Math.round(size.width), height: Math.round(size.height), scale: 2
        });
        status.textContent = 'Gambar siap diunduh.';
    } catch (error) {
        status.textContent = 'Gagal mengunduh gambar. Coba lagi setelah grafik tampil.';
    } finally {
        button.disabled = false;
    }
}
"""
    page = """<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><script src="plotly.min.js"></script>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px auto; max-width: 1300px; padding: 0 20px; color: #1e293b; }}
a {{ color: #2563eb; }}
.table {{ overflow: auto; max-height: 450px; margin: 16px 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; white-space: nowrap; }}
th {{ background: #f1f5f9; position: sticky; top: 0; }}
details {{ margin: 16px 0 32px; }}
summary {{ cursor: pointer; }}
.figure-actions {{ display: flex; align-items: center; gap: 12px; margin-top: 12px; }}
.figure-actions button {{ background: #2563eb; color: white; border: 0; border-radius: 6px; padding: 8px 12px; cursor: pointer; }}
.figure-actions button:disabled {{ opacity: 0.6; cursor: wait; }}
.download-status {{ font-size: 14px; }}
</style><script>{download_script}</script></head><body><h1>{title}</h1>{content}</body></html>"""
    path.write_text(page.format(
        title=escape(title), content=content, download_script=download_script,
    ), encoding="utf-8")


def write_result(problem, result, path):
    algorithm = result["algorithm"]
    name = ALGORITHM_NAMES.get(algorithm, algorithm)
    title = f"{path.stem} | {name}"
    parts = [
        "<p>Posisi paket di luar peti hanya ilustrasi; posisi state tetap None. "
        "Sel (x, y, z) mewakili [x, x+1) &times; [y, y+1) &times; [z, z+1). "
        "Warna abu-abu pada peta sel berarti kosong. Arahkan kursor untuk melihat ID paket.</p>"
        "<p>Atur sudut pandang 3D, zoom, atau lapisan z, lalu klik Unduh PNG (2x) "
        "pada grafik yang ingin disimpan. Gambar mengikuti tampilan grafik saat diunduh.</p>"
    ]
    for phase, label in [("initial_state", "Initial state"), ("final_state", "Final state")]:
        state = read_state(problem, result[phase])
        value_field = "initial_value" if phase == "initial_state" else "final_value"
        if evaluate(problem, state) != result[value_field]:
            raise ValueError(f"{path.stem}: {value_field} tidak cocok dengan nilai paket dalam state.")
        figure, packages, grid = state_view(problem, result[phase], label)
        parts.extend([
            f"<h2>{label}</h2>", figure_html(figure, f"{path.stem}_{phase}_3d"),
            figure_html(
                grid_view(problem, grid, f"{label}: seluruh sel peti"),
                f"{path.stem}_{phase}_grid",
            ),
            "<details><summary>Semua paket</summary>" + table_html(packages) + "</details>",
        ])
    parts.append("<h2>Hasil eksperimen</h2>")
    extra = result.get("extra", {})
    metrics = {
        "Algoritma": name,
        "Run": result.get("run_id", "-"),
        "Seed": result.get("seed", "-"),
        "Nilai objective awal": result["initial_value"],
        "Nilai objective akhir": result["final_value"],
        "Durasi pencarian (detik)": result["duration_seconds"],
        "Generasi dijalankan" if algorithm == "genetic_algorithm" else "Iterasi dijalankan":
            extra.get("total_iterations", result["iterations"]),
        "Alasan berhenti": result["stop_reason"],
    }
    if algorithm == "sideways":
        metrics["Sideways diterima"] = extra["sideways_moves"]
    elif algorithm == "random_restart":
        metrics["Jumlah restart"] = extra.get("restart_count", extra["num_searches"] - 1)
        metrics["Pencarian terbaik"] = extra["best_search"]
    elif algorithm == "simulated_annealing":
        metrics["Frekuensi stuck (episode)"] = extra.get("stuck_count", "Tidak dicatat")
        if "stuck_iterations" in extra:
            metrics["Iterasi dalam kondisi stuck"] = extra["stuck_iterations"]
    parts.append(table_html(pd.DataFrame(metrics.items(), columns=["Metrik", "Nilai"])))

    parameter_labels = {
        "population_size": "Jumlah populasi",
        "iterations": "Batas generasi GA",
        "maximum_sideways_move": "Maksimum sideways move",
        "maximum_restart": "Maksimum restart",
        "max_iterations": "Batas iterasi",
        "initial_temperature": "Suhu awal",
        "minimum_temperature": "Suhu minimum",
        "cooling_rate": "Faktor pendinginan",
        "stuck_patience": "Batas proposal tanpa perbaikan untuk deteksi stuck",
    }
    parameters = result.get("parameters", {})
    if parameters:
        parts.append(table_html(pd.DataFrame([
            (parameter_labels.get(key, key), value)
            for key, value in parameters.items()
        ], columns=["Parameter", "Nilai"])))
    notes = {
        "sideways": "Jumlah sideways memakai perpindahan yang diterima; titik datar terakhir dapat berarti berhenti.",
        "random_restart": "Initial state berasal dari Pencarian 0. Final state adalah hasil terbaik dari seluruh pencarian. Grafik memakai indeks riwayat kumulatif, termasuk titik awal setiap restart.",
        "simulated_annealing": "E adalah nilai objective state saat ini, bukan energi yang diminimalkan. Delta E adalah nilai proposal dikurangi nilai state sebelum iterasi. Final state adalah state terbaik yang ditemukan. Probabilitas proposal tidak menunjukkan keputusan penerimaannya.",
        "genetic_algorithm": "Initial state adalah individu terbaik pada populasi awal. Final state adalah individu terbaik sepanjang pencarian.",
    }
    if algorithm in notes:
        parts.append(f"<p>{notes[algorithm]}</p>")
    if algorithm == "simulated_annealing" and "stuck_definition" in extra:
        parts.append(f"<p>Definisi stuck: {escape(extra['stuck_definition'])}.</p>")
    parts.append(figure_html(algorithm_view(result), f"{path.stem}_experiment"))
    if algorithm == "random_restart":
        parts.append(table_html(pd.DataFrame([
            {
                "Pencarian (0 = awal)": search["search_id"],
                "Iterasi": search["iterations"],
                "Nilai awal": search["initial_value"],
                "Nilai akhir": search["final_value"],
                "Alasan berhenti": search["stop_reason"],
            }
            for search in extra["restarts"]
        ])))
    write_page(path, title, "".join(parts))


def main():
    parser = argparse.ArgumentParser(description="Buat satu HTML per JSON hasil pencarian, dengan nama file yang sama.")
    parser.add_argument("--input", required=True, type=Path, help="JSON permasalahan yang digunakan saat pencarian")
    parser.add_argument("--results", type=Path, default=Path("output"), help="File JSON hasil atau direktori hasil")
    parser.add_argument("--output-dir", type=Path, default=Path("output/visualizations"))
    args = parser.parse_args()
    files = sorted(args.results.glob("*.json")) if args.results.is_dir() else [args.results]
    if not files:
        parser.error("Tidak ada JSON hasil pencarian pada direktori tersebut.")

    try:
        problem = load_problem(args.input)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
        for source in files:
            result = json.loads(source.read_text(encoding="utf-8-sig"))
            destination = args.output_dir / source.with_suffix(".html").name
            write_result(problem, result, destination)
            print(f"Dibuat: {destination.resolve()}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(f"Selesai: {len(files)} HTML. Buka file HTML hasil run yang ingin dilihat.")


if __name__ == "__main__":
    main()
