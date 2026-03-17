"""
Plotting utilities for CO2 refrigeration systems.

Provides T-s diagrams, log(p)-h diagrams, and efficiency matrix heatmaps
for transcritical CO2 cycles. Adapted from HeatPumpStudy plotting methods
with CO2/R744 specific extensions (supercritical region rendering).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from fluprodia import FluidPropertyDiagram
from typing import Optional, Dict, Tuple, List


# Ecalia brand colors
ECALIA_BLUE = "#00395b"
ECALIA_TEAL = "#74adc1"
ECALIA_RED = "#b54036"
ECALIA_ORANGE = "#ec6707"
ECALIA_GRAY = "#999999"

CYCLE_COLOR = ECALIA_RED
EXPANDER_COLOR = ECALIA_ORANGE
BASELINE_COLOR = ECALIA_BLUE


def plot_ts_diagram(
    results: dict,
    fluid: str = "CO2",
    filename: Optional[str] = None,
    title: Optional[str] = None,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    y_min: Optional[float] = None,
    y_max: Optional[float] = None,
    color: str = CYCLE_COLOR,
    model=None,
    fig=None,
    ax=None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot T-s diagram with fluid property background isolines.

    When *model* is provided, parallel / flash-gas paths are drawn dashed
    in a lighter shade, DropletSeparator separation lines are included,
    and numbered state point labels are annotated — mirroring the behaviour
    of ``plot_logph_diagram``.

    If *fig* and *ax* are provided the diagram is drawn onto the existing
    axis (useful for subplot grids); otherwise a new figure is created.

    Args:
        results: Dict from RefrigerationStudy.get_results().
        fluid: CoolProp fluid name (default "CO2").
        filename: If provided, saves to this path (.svg appended).
        title: Plot title.
        model: Optional solved TESPy model for parallel-path colouring,
               flash drum lines and state point labels.
        fig: Optional existing Figure (for subplot use).
        ax: Optional existing Axes (for subplot use).
    """
    diagram = FluidPropertyDiagram(fluid)
    diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")

    states = model.get_state_points() if model is not None else {}

    # Calculate isolines for result data
    result_dict = {}
    for key, data in results.items():
        result_dict[key] = dict(data)  # copy
        result_dict[key]["datapoints"] = _clip_isoline_outliers(
            diagram.calc_individual_isoline(**data), clip_key="s"
        )

    # Auto-determine limits (include flash drum state points)
    if any(v is None for v in [x_min, x_max, y_min, y_max]):
        s_vals, T_vals = [], []
        for data in result_dict.values():
            s_vals.extend(data["datapoints"]["s"])
            T_vals.extend(data["datapoints"]["T"])
        for st in states.values():
            if "s" in st:
                s_vals.append(st["s"])
            if "T" in st:
                T_vals.append(st["T"])
        x_min = min(s_vals) - 0.1 if x_min is None else x_min
        x_max = max(s_vals) + 0.1 if x_max is None else x_max
        y_min = min(T_vals) - 15 if y_min is None else y_min
        y_max = max(T_vals) + 15 if y_max is None else y_max

    T_iso = np.arange(y_min, y_max + 1, 10)
    Q_iso = np.linspace(0, 1, 41)

    external_ax = ax is not None
    if not external_ax:
        fig, ax = plt.subplots(1, figsize=(10, 6))
    diagram.set_isolines(T=T_iso, Q=Q_iso)
    diagram.calc_isolines()
    mydata = {"Q": {"values": Q_iso, "label_position": 0.20}, "T": {"values": T_iso}}
    diagram.draw_isolines(
        diagram_type="Ts", fig=fig, ax=ax,
        x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
        isoline_data=mydata,
    )

    par_color = _lighten_color(color, 0.4) if model is not None else color
    for key, data in result_dict.items():
        dp = data["datapoints"]
        par = _is_parallel(key) if model is not None else False
        c = par_color if par else color
        lw = 1.8 if par else 2.0
        ls = '--' if par else '-'
        ax.plot(dp["s"], dp["T"], color=c, linewidth=lw, linestyle=ls)
        ax.scatter(dp["s"][0], dp["T"][0], color=c, s=30, zorder=5)

    # ── Draw DropletSeparator separation lines ──
    if model is not None:
        _draw_flash_drum_lines_ts(model, states, diagram, ax, color, par_color)

    # ── Annotate numbered state points ──
    if model is not None:
        _annotate_state_points(states, ax, diagram_type="Ts")

    if title:
        ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Entropy s [kJ/(kg·K)]")
    ax.set_ylabel("Temperature T [°C]")

    if filename and not external_ax:
        fig.savefig(f"{filename}.svg", bbox_inches="tight")
    return fig, ax


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers for log(p)-h diagrams
# ─────────────────────────────────────────────────────────────────────────────

def _is_parallel(key: str) -> bool:
    """Classify a result key or connection label as parallel/flash-gas path.

    Rules:
    - Components with 'fgbv' or 'parallel_compressor' → parallel
    - 'flash_drum' → 'iwt_flashgas' (vapor outlet to flash-gas IWT) → parallel
    - Dual-index _2 of 'iwt_flashgas', 'hp_merge', 'suction_merge' → parallel
    - Everything else (including _1 of dual-index components) → main
    """
    k = key.lower()
    if any(kw in k for kw in ("fgbv", "parallel_compressor")):
        return True
    # Flash drum vapor outlet to IWT (expander topology) is also a parallel path
    if "flash_drum" in k and "iwt_flashgas" in k:
        return True
    if k.endswith("_2"):
        base = k.rsplit("_", 1)[0]
        if any(b in base for b in ("iwt_flashgas", "hp_merge", "suction_merge")):
            return True
    return False


def _draw_flash_drum_lines(model, states, diagram, ax, main_color,
                           par_color=None, diagram_type="logph"):
    """Draw DropletSeparator isobaric separation lines on a diagram axis.

    The DropletSeparator has no ``get_plotting_data()`` in TESPy (it's a
    node, not a process).  This draws isobaric lines from the two-phase
    inlet to each saturated outlet at *p_medium*.

    Args:
        diagram_type: ``'logph'`` plots ``(h, p)``; ``'Ts'`` plots ``(s, T)``.
    """
    if par_color is None:
        par_color = _lighten_color(main_color, 0.4)
    from tespy.components import DropletSeparator as _DS
    x_key, y_key = ("h", "p") if diagram_type == "logph" else ("s", "T")
    for name, comp in model.comp.items():
        if not isinstance(comp, _DS):
            continue
        inlet_label = None
        outlet_labels = []
        for label in model.conn:
            src, dst = label.split("-")
            if dst == name:
                inlet_label = label
            elif src == name:
                outlet_labels.append(label)

        if inlet_label and inlet_label in states:
            s_in = states[inlet_label]
            for out_label in outlet_labels:
                if out_label not in states:
                    continue
                s_out = states[out_label]
                iso_data = {
                    "isoline_property": "p",
                    "isoline_value": s_in["p"],
                    "starting_point_property": "h",
                    "starting_point_value": s_in["h"],
                    "ending_point_property": "h",
                    "ending_point_value": s_out["h"],
                }
                dp = diagram.calc_individual_isoline(**iso_data)
                par = _is_parallel(out_label)
                c = par_color if par else main_color
                ls = '--' if par else '-'
                ax.plot(dp[x_key], dp[y_key], color=c, linewidth=2.0, linestyle=ls)
                ax.scatter(dp[x_key][-1], dp[y_key][-1], color=c, s=25, zorder=5)


# Keep legacy alias so existing imports don't break
_draw_flash_drum_lines_ts = lambda model, states, diagram, ax, mc, pc=None: \
    _draw_flash_drum_lines(model, states, diagram, ax, mc, pc, diagram_type="Ts")


def _draw_logph_background(diagram, fig, ax, x_min, x_max, y_min, y_max):
    """Draw the two-phase dome, T isolines, and Q isolines as background.

    Q labels are positioned at 0.20 (near the low-pressure end of the dome)
    to keep them away from the main operating region.
    Uses fewer Q isolines for a cleaner appearance.
    """
    T_iso = np.arange(-60, 201, 10)
    Q_iso = np.linspace(0, 1, 41)
    diagram.set_isolines(T=T_iso, Q=Q_iso)
    diagram.calc_isolines()
    mydata = {
        "Q": {"values": Q_iso, "label_position": 0.20},
        "T": {"values": T_iso},
    }
    diagram.draw_isolines(
        diagram_type="logph", fig=fig, ax=ax,
        isoline_data=mydata,
        x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
    )


def _clip_isoline_outliers(dp, clip_key="h"):
    """Remove endpoint outliers from a fluprodia isoline.

    fluprodia's ``calc_individual_isoline`` occasionally finds the wrong
    CoolProp branch at boundary states (e.g. exactly on the saturation
    line).  This manifests as the first or last data point having a
    property value far away from its neighbour while the rest of the curve
    is smooth.  Clipping these points avoids visual artefacts ('dead
    lines') on log(p)-h and T-s diagrams.

    Args:
        dp: Dict returned by ``diagram.calc_individual_isoline()``.
        clip_key: Property key used to detect outliers (default ``"h"``).
    """
    vals = np.array(dp[clip_key])
    if len(vals) < 4:
        return dp
    # Average absolute step (excluding the first/last segment)
    inner_steps = np.abs(np.diff(vals[1:-1]))
    avg_step = np.mean(inner_steps) if len(inner_steps) > 0 else 0.0
    threshold = max(avg_step * 10, 20)
    start = 0
    end = len(vals)
    if abs(vals[0] - vals[1]) > threshold:
        start = 1
    if abs(vals[-1] - vals[-2]) > threshold:
        end = len(vals) - 1
    if start == 0 and end == len(vals):
        return dp
    clipped = {}
    for k, v in dp.items():
        arr = np.array(v)
        clipped[k] = arr[start:end].tolist()
    return clipped


def _draw_model_on_axis(model, diagram, ax, color, linewidth=2.0,
                        label=None, show_flash_drum=True):
    """Draw a single model's cycle lines on an existing axis.

    Main cycle paths are drawn solid; parallel/flash-gas paths are drawn
    dashed in a lighter shade of the same color. Flash drum separation
    lines connect the two-phase inlet to the liquid/vapor outlets.

    Args:
        model: Solved TESPy model.
        diagram: FluidPropertyDiagram instance (already configured).
        ax: Matplotlib axis to draw on.
        color: Line color for main path.
        linewidth: Line width.
        label: Legend label (only applied to first main-path line).
        show_flash_drum: If True, draw DropletSeparator separation lines.
    """
    results = model.get_results()
    states = model.get_state_points()
    par_color = _lighten_color(color, 0.4)

    first_main = True
    first_par = True
    for key, data in results.items():
        dp = _clip_isoline_outliers(diagram.calc_individual_isoline(**data))
        par = _is_parallel(key)

        if par:
            lbl = (f"{label} (Flash-Gas)" if label and first_par else None)
            ax.plot(dp["h"], dp["p"], color=par_color, linewidth=linewidth * 0.8,
                    linestyle='--', label=lbl)
            first_par = False
        else:
            lbl = label if first_main else None
            ax.plot(dp["h"], dp["p"], color=color, linewidth=linewidth,
                    linestyle='-', label=lbl)
            first_main = False

    if show_flash_drum:
        _draw_flash_drum_lines(model, states, diagram, ax, color, par_color)


def _lighten_color(hex_color, factor=0.5):
    """Lighten a hex color by blending with white."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f'#{r:02x}{g:02x}{b:02x}'


def _deduplicate_state_points(states, diagram_type="logph"):
    """Return a deduplicated list of ``(number, conn_label, x, y)`` tuples.

    Spatially close points are merged so diagram annotations and the
    printed legend use the same numbering.
    """
    plotted = []
    legend = []
    n = 1
    for label, st in states.items():
        if diagram_type == "logph":
            x, y = st["h"], st["p"]
        else:
            x, y = st["s"], st["T"]
        too_close = False
        for px, py in plotted:
            if diagram_type == "logph":
                if abs(x - px) < 8 and abs(np.log10(max(y, 0.1)) - np.log10(max(py, 0.1))) < 0.03:
                    too_close = True
                    break
            else:
                if abs(x - px) < 0.05 and abs(y - py) < 3:
                    too_close = True
                    break
        if too_close:
            continue
        plotted.append((x, y))
        legend.append((n, label, x, y))
        n += 1
    return legend


def _annotate_state_points(states, ax, diagram_type="logph", fontsize=7):
    """Draw numbered state point labels on a diagram axis.

    Uses ``_deduplicate_state_points`` so numbering is consistent with
    ``print_state_point_legend``.

    Returns:
        List of ``(number, connection_label)`` tuples.
    """
    if not states:
        return []

    legend = _deduplicate_state_points(states, diagram_type)
    for num, label, x, y in legend:
        ax.annotate(
            str(num), (x, y),
            textcoords="offset points", xytext=(6, 6),
            fontsize=fontsize, fontweight="bold",
            color=ECALIA_BLUE,
            bbox=dict(
                boxstyle="circle,pad=0.15", fc="white", ec=ECALIA_BLUE,
                alpha=0.85, lw=0.5,
            ),
            zorder=10,
        )
    return [(n, lbl) for n, lbl, *_ in legend]


def _annotate_canonical(model, ax, fontsize=7, x_color=None):
    """Annotate canonical state points on a log(p)-h diagram.

    Uses ``model.get_canonical_state_points()`` for consistent numbering
    across different booster topologies (IWT, PV, etc.).

    Returns:
        List of ``(num, description, h, p)`` tuples for table / legend.
    """
    canon = model.get_canonical_state_points()
    states = model.get_state_points()

    result = []
    placed = []  # [(h, p, [nums])]

    for num, conn_label, desc in canon:
        if conn_label not in states:
            continue
        st = states[conn_label]
        h, p = st['h'], st['p']
        result.append((num, desc, h, p))

        # Merge annotation if another point is at the same (h, p) location
        merged = False
        for i, (ph, pp, nums) in enumerate(placed):
            if (abs(h - ph) < 3
                    and abs(np.log10(max(p, 0.1)) - np.log10(max(pp, 0.1))) < 0.02):
                nums.append(num)
                merged = True
                break
        if not merged:
            placed.append((h, p, [num]))

    # Build lookup: canonical number → connection label (for x retrieval)
    num_to_conn = {num: conn_label for num, conn_label, _ in canon}

    for h, p, nums in placed:
        label = ",".join(str(n) for n in nums)
        use_circle = len(label) <= 2
        ax.annotate(
            label, (h, p),
            textcoords="offset points", xytext=(6, 6),
            fontsize=fontsize, fontweight="bold",
            color=ECALIA_BLUE,
            bbox=dict(
                boxstyle="circle,pad=0.15" if use_circle else "round,pad=0.15",
                fc="white", ec=ECALIA_BLUE, alpha=0.85, lw=0.5,
            ),
            zorder=10,
        )

        # Show vapor quality at state 5 (flash drum inlet)
        if 5 in nums:
            conn5 = num_to_conn.get(5)
            if conn5 and conn5 in states:
                x_val = states[conn5].get('x')
                # TESPy returns x=-1 outside two-phase → compute from CoolProp
                if x_val is None or x_val < 0 or x_val > 1:
                    try:
                        from CoolProp.CoolProp import PropsSI
                        x_val = PropsSI(
                            "Q", "H", states[conn5]['h'] * 1e3,
                            "P", states[conn5]['p'] * 1e5, "CO2")
                    except Exception:
                        x_val = None
                if x_val is not None and 0 <= x_val <= 1:
                    ann_color = x_color if x_color else '#333333'
                    ann_ec = x_color if x_color else '#999999'
                    ax.annotate(
                        f"x = {x_val:.2f}", (h, p),
                        textcoords="offset points", xytext=(20, -12),
                        fontsize=fontsize, fontstyle="italic",
                        color=ann_color,
                        arrowprops=dict(arrowstyle='->', color=ann_color, lw=0.7),
                        bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                  ec=ann_ec, alpha=0.9, lw=0.8),
                        zorder=10,
                    )

    return result


# ── Readable component name mapping ──
_COMPONENT_NAMES = {
    "cycle_closer": "Kreislauf",
    "nk_compressor": "NK-Kompressor",
    "gas_cooler": "Gaskühler",
    "hpev": "HD-Expansionsventil",
    "flash_drum": "Sammler",
    "mpev": "MD-Ventil (Flüssigkeit)",
    "nk_evaporator": "NK-Verdampfer",
    "fgbv": "Flash-Gas-Bypass-Ventil",
    "suction_merge": "Saugmischer",
    "iwt_flashgas": "IWT (Flash-Gas)",
    "parallel_compressor": "Parallelverdichter",
    "hp_merge": "HD-Mischer",
}


def print_state_point_legend(model):
    """Print a legend mapping diagram state-point numbers to processes.

    Uses ``_deduplicate_state_points`` so numbering matches the circled
    labels on the diagrams.

    Args:
        model: Solved TESPy RefrigerationStudy instance.
    """
    states = model.get_state_points()
    if not states:
        print("Keine Zustandspunkte vorhanden.")
        return

    legend = _deduplicate_state_points(states, diagram_type="logph")

    # Build process list: if point i's destination == point j's source → process
    processes = []
    for i, (num_i, label_i, *_) in enumerate(legend):
        _, dst_i = label_i.split("-", 1)
        for j, (num_j, label_j, *_) in enumerate(legend):
            if j == i:
                continue
            src_j, _ = label_j.split("-", 1)
            if dst_i == src_j:
                readable = _COMPONENT_NAMES.get(dst_i, dst_i)
                processes.append((num_i, num_j, readable))

    print("\nZustandspunkt-Zuordnung:")
    print("-" * 42)
    for num, conn_label, *_ in legend:
        src, dst = conn_label.split("-", 1)
        src_r = _COMPONENT_NAMES.get(src, src)
        dst_r = _COMPONENT_NAMES.get(dst, dst)
        print(f"  {num:2d}   {src_r} → {dst_r}")

    if processes:
        print(f"\nProzesse:")
        print("-" * 42)
        for n1, n2, name in sorted(processes):
            print(f"  {n1}→{n2}  {name}")


def plot_logph_overlay(
    models: List[Tuple],
    fluid: str = "CO2",
    filename: Optional[str] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 7),
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot log(p)-h overlay comparing multiple model configurations.

    Each model is drawn with its own colour on the same axis.  Main cycle
    paths are solid; parallel / flash-gas paths are shown dashed in a
    lighter shade.  Flash drum separation lines are included.

    Args:
        models: List of (model, label, color, linewidth) tuples.
    """
    diagram = FluidPropertyDiagram(fluid)
    diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")

    # Compute axis limits across all models
    h_vals, p_vals = [], []
    for model, *_ in models:
        results = model.get_results()
        states = model.get_state_points()
        for key, data in results.items():
            dp = _clip_isoline_outliers(diagram.calc_individual_isoline(**data))
            h_vals.extend(dp["h"])
            p_vals.extend(dp["p"])
        for st in states.values():
            h_vals.append(st["h"])
            p_vals.append(st["p"])

    x_min = min(h_vals) - 30
    x_max = max(h_vals) + 30
    y_min = min(p_vals) * 0.7
    y_max = max(p_vals) * 1.3

    fig, ax = plt.subplots(1, figsize=figsize)
    _draw_logph_background(diagram, fig, ax, x_min, x_max, y_min, y_max)

    for model, label, color, lw in models:
        _draw_model_on_axis(
            model, diagram, ax, color,
            linewidth=lw, label=label,
            show_flash_drum=True,
        )

    ax.legend(fontsize=9)
    if title:
        ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Enthalpy h [kJ/kg]")
    ax.set_ylabel("Pressure p [bar]")

    fig.tight_layout()
    if filename:
        fig.savefig(f"{filename}.svg", bbox_inches="tight")
    return fig, ax


def plot_logph_diagram(
    results: dict,
    fluid: str = "CO2",
    filename: Optional[str] = None,
    title: Optional[str] = None,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    y_min: Optional[float] = None,
    y_max: Optional[float] = None,
    color: str = CYCLE_COLOR,
    model=None,
    fig=None,
    ax=None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot log(p)-h diagram with fluid property background.

    Particularly important for CO2 transcritical cycles where the
    supercritical region is clearly visible. When a model is provided,
    also draws DropletSeparator separation lines, distinguishes
    main vs. parallel (flash-gas / PV) paths, and annotates numbered
    state points.

    If *fig* and *ax* are provided the diagram is drawn onto the existing
    axis (useful for subplot grids); otherwise a new figure is created.

    Args:
        results: Dict from RefrigerationStudy.get_results().
        model: Optional solved TESPy model — enables flash drum lines,
               parallel path coloring and state point labels.
        fig: Optional existing Figure (for subplot use).
        ax: Optional existing Axes (for subplot use).
    """
    diagram = FluidPropertyDiagram(fluid)
    diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")

    # If model supplied, also grab state points for flash drum rendering
    states = model.get_state_points() if model is not None else {}

    result_dict = {}
    for key, data in results.items():
        result_dict[key] = dict(data)
        result_dict[key]["datapoints"] = _clip_isoline_outliers(
            diagram.calc_individual_isoline(**data)
        )

    if any(v is None for v in [x_min, x_max, y_min, y_max]):
        h_vals, p_vals = [], []
        for data in result_dict.values():
            h_vals.extend(data["datapoints"]["h"])
            p_vals.extend(data["datapoints"]["p"])
        for st in states.values():
            h_vals.append(st["h"])
            p_vals.append(st["p"])
        x_min = min(h_vals) - 30 if x_min is None else x_min
        x_max = max(h_vals) + 30 if x_max is None else x_max
        y_min = min(p_vals) * 0.7 if y_min is None else y_min
        y_max = max(p_vals) * 1.3 if y_max is None else y_max

    external_ax = ax is not None
    if not external_ax:
        fig, ax = plt.subplots(1, figsize=(10, 6))
    _draw_logph_background(diagram, fig, ax, x_min, x_max, y_min, y_max)

    par_color = _lighten_color(color, 0.4) if model is not None else color
    for key, data in result_dict.items():
        dp = data["datapoints"]
        par = _is_parallel(key) if model is not None else False
        c = par_color if par else color
        lw = 1.8 if par else 2.0
        ls = '--' if par else '-'
        ax.plot(dp["h"], dp["p"], color=c, linewidth=lw, linestyle=ls)
        ax.scatter(dp["h"][0], dp["p"][0], color=c, s=30, zorder=5)

    # ── Draw DropletSeparator separation lines (if model provided) ──
    if model is not None:
        _draw_flash_drum_lines(model, states, diagram, ax, color, par_color)

    # ── Annotate numbered state points ──
    if model is not None:
        _annotate_state_points(states, ax, diagram_type="logph")

    if title:
        ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Enthalpy h [kJ/kg]")
    ax.set_ylabel("Pressure p [bar]")

    if filename and not external_ax:
        fig.savefig(f"{filename}.svg", bbox_inches="tight")
    return fig, ax


def plot_efficiency_matrix(
    matrix: np.ndarray,
    row_labels: List[str],
    col_labels: List[str],
    filename: Optional[str] = None,
    title: str = "COP Comparison",
    value_label: str = "COP",
    cmap: str = "RdYlGn",
    fmt: str = ".2f",
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot a heatmap of COP or efficiency values.

    Args:
        matrix: 2D array, rows = configurations, cols = operating points (or vice versa).
        row_labels: Labels for matrix rows.
        col_labels: Labels for matrix columns.
        filename: Save path (appends .png).
        title: Plot title.
        value_label: Colorbar label.
    """
    fig, ax = plt.subplots(figsize=(max(8, len(col_labels) * 1.5), max(4, len(row_labels) * 0.8)))
    im = ax.imshow(matrix, cmap=cmap, aspect="auto")

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel(value_label, rotation=-90, va="bottom")

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(row_labels, fontsize=9)

    # Annotate cells
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = matrix[i, j]
            text_color = "white" if val < (matrix.min() + matrix.max()) / 2 else "black"
            ax.text(j, i, f"{val:{fmt}}", ha="center", va="center",
                    color=text_color, fontweight="bold", fontsize=10)

    ax.set_title(title, fontsize=13, fontweight="bold")
    fig.tight_layout()

    if filename:
        fig.savefig(f"{filename}.png", dpi=150, bbox_inches="tight")
    return fig, ax


def plot_logph_with_massflow(
    model,
    fluid: str = "CO2",
    filename: Optional[str] = None,
    title: Optional[str] = None,
    color: str = CYCLE_COLOR,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot log(p)-h diagram with mass flow fraction annotations on each path.

    Draws the main cycle AND all branch paths (flash gas bypass, IWT,
    parallel compressor) with mass flow percentages. Correctly handles:
    - DropletSeparator separation lines (two-phase → liquid / vapor at p_medium)
    - Dual-side components: HeatExchanger _1 = main (warm), _2 = parallel (cold)
    - Merge components: _1 = main (NK), _2 = parallel (PV/flash-gas)

    Args:
        model: A solved TESPy RefrigerationStudy subclass instance.
        fluid: CoolProp fluid name.
        filename: Save path (appends .svg).
        title: Plot title.
    """
    diagram = FluidPropertyDiagram(fluid)
    diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")

    results = model.get_results()
    states = model.get_state_points()

    # Total mass flow for normalization (max across all connections)
    m_total = max((abs(st["m"]) for st in states.values()), default=1.0)
    if m_total == 0:
        m_total = 1.0

    # Compute fluprodia data points for all component isolines
    result_dict = {}
    for key, data in results.items():
        result_dict[key] = dict(data)
        result_dict[key]["datapoints"] = _clip_isoline_outliers(
            diagram.calc_individual_isoline(**data)
        )

    # Auto-determine axis limits (include all state points for flash drum)
    h_vals, p_vals = [], []
    for data in result_dict.values():
        h_vals.extend(data["datapoints"]["h"])
        p_vals.extend(data["datapoints"]["p"])
    for st in states.values():
        h_vals.append(st["h"])
        p_vals.append(st["p"])
    x_min = min(h_vals) - 30
    x_max = max(h_vals) + 30
    y_min = min(p_vals) * 0.7
    y_max = max(p_vals) * 1.3

    fig, ax = plt.subplots(1, figsize=(12, 7))
    _draw_logph_background(diagram, fig, ax, x_min, x_max, y_min, y_max)

    # ── Draw component isolines ──
    par_color = _lighten_color(color, 0.4)
    for key, data in result_dict.items():
        dp = data["datapoints"]
        par = _is_parallel(key)
        c = par_color if par else color
        lw = 1.8 if par else 2.0
        ls = '--' if par else '-'
        ax.plot(dp["h"], dp["p"], color=c, linewidth=lw, linestyle=ls)
        ax.scatter(dp["h"][0], dp["p"][0], color=c, s=25, zorder=5)

    # ── Draw DropletSeparator separation lines ──
    _draw_flash_drum_lines(model, states, diagram, ax, color, par_color)

    # ── Mass flow annotations ──
    plotted_positions = []
    for label, st in states.items():
        h_pt, p_pt = st["h"], st["p"]
        m_frac = abs(st["m"]) / m_total

        # Skip close-to-duplicate annotations
        too_close = False
        for ph, pp in plotted_positions:
            if abs(h_pt - ph) < 12 and abs(np.log10(p_pt) - np.log10(pp)) < 0.04:
                too_close = True
                break
        if too_close:
            continue
        plotted_positions.append((h_pt, p_pt))

        # Only annotate non-trivial mass flow fractions (not ~ 1.0)
        if abs(m_frac - 1.0) > 0.02:
            ax.annotate(
                f"{m_frac:.2f}",
                (h_pt, p_pt),
                textcoords="offset points",
                xytext=(8, -12),
                fontsize=8,
                fontweight="bold",
                color=ECALIA_TEAL if m_frac < 0.95 else ECALIA_GRAY,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8),
            )

    # ── Legend ──
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=color, linewidth=2, label="Hauptkreislauf"),
        Line2D([0], [0], color=par_color, linewidth=1.8, linestyle='--',
               label="Flash-Gas / PV Pfad"),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    if title:
        ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Enthalpy h [kJ/kg]")
    ax.set_ylabel("Pressure p [bar]")

    fig.tight_layout()
    if filename:
        fig.savefig(f"{filename}.svg", bbox_inches="tight")
    return fig, ax


def plot_cop_comparison_bar(
    cop_data: Dict[str, Dict[str, float]],
    filename: Optional[str] = None,
    title: str = "COP Comparison by Operating Point",
) -> Tuple[plt.Figure, plt.Axes]:
    """Bar chart comparing COP across configurations for each operating point.

    Args:
        cop_data: {config_name: {op_point_name: cop_value, ...}, ...}
    """
    configs = list(cop_data.keys())
    op_points = list(cop_data[configs[0]].keys())
    n_configs = len(configs)
    n_ops = len(op_points)

    colors = [BASELINE_COLOR, ECALIA_TEAL, ECALIA_ORANGE, ECALIA_RED, ECALIA_GRAY]

    x = np.arange(n_ops)
    width = 0.8 / n_configs

    fig, ax = plt.subplots(figsize=(max(10, n_ops * 2), 6))

    for i, config in enumerate(configs):
        values = [cop_data[config].get(op, 0) for op in op_points]
        bars = ax.bar(x + i * width - 0.4 + width / 2, values, width,
                      label=config, color=colors[i % len(colors)])
        # Add value labels on bars
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                        f"{val:.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Operating Point")
    ax.set_ylabel("COP")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(op_points, rotation=30, ha="right", fontsize=9)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    if filename:
        fig.savefig(f"{filename}.png", dpi=150, bbox_inches="tight")
    return fig, ax


# ─────────────────────────────────────────────────────────────────────────────
# High-level convenience API (reduces notebook boilerplate)
# ─────────────────────────────────────────────────────────────────────────────

import re as _re
import math as _math


def sanitize_filename(name: str) -> str:
    """Convert a human-readable label into a filesystem-safe string.

    Spaces become underscores, parentheses/special chars are stripped.

    >>> sanitize_filename("Baseline (V+V)")
    'Baseline_V+V'
    """
    name = name.replace(" ", "_")
    name = _re.sub(r"[()\\/:*?\"<>|]", "", name)
    return name


def plot_model(
    model,
    diagram_type: str = "logph",
    *,
    title: Optional[str] = None,
    filename: Optional[str] = None,
    color: str = CYCLE_COLOR,
    fig=None,
    ax=None,
    show_legend: bool = False,
    **kwargs,
) -> Tuple[plt.Figure, plt.Axes]:
    """One-call diagram from a solved TESPy model (no manual ``get_results``).

    Args:
        model: Solved RefrigerationStudy instance.
        diagram_type: ``'logph'``, ``'Ts'`` or ``'massflow'``.
        title: Plot title (auto-generated from model class if ``None``).
        filename: Save path (extension auto-appended, ``None`` = don't save).
        color: Cycle line color.
        fig / ax: External Figure / Axes for subplot embedding.
        show_legend: If True, print the state-point legend to stdout.
        **kwargs: Forwarded to the underlying plot function.

    Returns:
        ``(fig, ax)`` tuple.
    """
    results = model.get_results()

    if diagram_type == "logph":
        fig, ax = plot_logph_diagram(
            results, model=model, title=title, filename=filename,
            color=color, fig=fig, ax=ax, **kwargs,
        )
    elif diagram_type == "Ts":
        fig, ax = plot_ts_diagram(
            results, model=model, title=title, filename=filename,
            color=color, fig=fig, ax=ax, **kwargs,
        )
    elif diagram_type == "massflow":
        fig, ax = plot_logph_with_massflow(
            model, title=title, filename=filename, color=color, **kwargs,
        )
    else:
        raise ValueError(f"Unknown diagram_type {diagram_type!r}. "
                         f"Use 'logph', 'Ts', or 'massflow'.")

    if show_legend:
        print_state_point_legend(model)
    return fig, ax


def plot_model_grid(
    models: Dict[str, object],
    diagram_type: str = "logph",
    *,
    cols: int = 2,
    figsize: Optional[Tuple[float, float]] = None,
    filename: Optional[str] = None,
    color: str = CYCLE_COLOR,
    show_legend: bool = False,
    **kwargs,
) -> Tuple[plt.Figure, np.ndarray]:
    """Plot a grid of diagrams — one per model.

    Args:
        models: ``{subplot_title: solved_model, ...}`` ordered dict.
        diagram_type: ``'logph'``, ``'Ts'`` or ``'massflow'``.
        cols: Number of columns in the grid.
        figsize: Override figure size (auto-scaled by default).
        filename: Save path (extension auto-appended).
        color: Cycle line color.
        show_legend: If True, print the state-point legend for the first model.
        **kwargs: Forwarded to the underlying plot function.

    Returns:
        ``(fig, axes)`` — Figure and 2-D axes array.
    """
    n = len(models)
    rows = _math.ceil(n / cols)
    if figsize is None:
        figsize = (10 * cols, 6 * rows)

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    axes_flat = np.atleast_2d(axes).reshape(-1)

    for idx, (title, model) in enumerate(models.items()):
        ax = axes_flat[idx]
        plot_model(model, diagram_type, title=title, color=color,
                   fig=fig, ax=ax, **kwargs)

    # Hide unused axes
    for idx in range(n, len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.tight_layout()
    if filename:
        ext = ".svg" if diagram_type in ("logph", "Ts") else ".png"
        fig.savefig(f"{filename}{ext}", bbox_inches="tight",
                    dpi=150 if ext == ".png" else None)

    if show_legend and models:
        first_model = next(iter(models.values()))
        print_state_point_legend(first_model)

    return fig, axes


def plot_comparison_grid(
    comparisons: List[Tuple],
    *,
    figsize: Optional[Tuple[float, float]] = None,
    filename: Optional[str] = None,
    suptitle: Optional[str] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """Plot side-by-side log(p)-h overlays comparing model pairs.

    Replaces the manual ``_draw_logph_background`` / ``_draw_model_on_axis``
    pattern — no private-API imports needed in notebooks.

    Args:
        comparisons: List of ``(title, model_a, model_b,
                     color_a, color_b)`` tuples. ``model_b`` may be None
                     (only *model_a* is drawn).
        figsize: Override figure size.
        filename: Save path (.svg appended).
        suptitle: Figure super-title.

    Returns:
        ``(fig, axes)`` tuple.
    """
    n = len(comparisons)
    if figsize is None:
        figsize = (7 * n, 6)

    fig, axes = plt.subplots(1, n, figsize=figsize)
    if n == 1:
        axes = np.array([axes])
    axes_flat = axes.reshape(-1)

    for idx, (title, m1, m2, c1, c2) in enumerate(comparisons):
        diagram = FluidPropertyDiagram("CO2")
        diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")

        # Compute axis limits across both models
        h_vals, p_vals = [], []
        for mdl in [m1, m2]:
            if mdl is None:
                continue
            for _k, data in mdl.get_results().items():
                dp = _clip_isoline_outliers(diagram.calc_individual_isoline(**data))
                h_vals.extend(dp["h"])
                p_vals.extend(dp["p"])
            for st in mdl.get_state_points().values():
                h_vals.append(st["h"])
                p_vals.append(st["p"])

        ax = axes_flat[idx]
        _draw_logph_background(
            diagram, fig, ax,
            min(h_vals) - 30, max(h_vals) + 30,
            min(p_vals) * 0.7, max(p_vals) * 1.3,
        )
        # Determine labels from model class or fallback
        lbl1 = getattr(m1, '_label', None) or m1.__class__.__name__
        lbl2 = getattr(m2, '_label', None) or m2.__class__.__name__ if m2 else None
        _draw_model_on_axis(m1, diagram, ax, c1, linewidth=1.5, label=lbl1)
        if m2 is not None:
            _draw_model_on_axis(m2, diagram, ax, c2, linewidth=2.5, label=lbl2)

        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.legend(fontsize=8)

    if suptitle:
        fig.suptitle(suptitle, fontweight="bold", fontsize=13)
    fig.tight_layout()
    if filename:
        fig.savefig(f"{filename}.svg", bbox_inches="tight")
    return fig, axes