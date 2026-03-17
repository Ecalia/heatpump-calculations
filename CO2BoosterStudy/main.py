"""
CO2 Booster Efficiency Study — Main Entry Point

Runs all simulation scenarios and generates comparison outputs.
Calibrated against BITZER Software v7.1.2 operating points from
Kälte Fischer GmbH (Lötzsch, 26.02.2026).
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.operating_points import (
    ALL_OPERATING_POINTS,
    OP_SUMMER_NO_PV,
    OP_SUMMER_WITH_PV,
    OP_TRANSITION_NO_PV,
    OP_WRG_NO_PV,
)
from src.co2_booster import CO2BoosterFlashgas, CO2BoosterFlashgasIWT, CO2BoosterParallel
from src.plotting import (
    plot_logph_diagram,
    plot_ts_diagram,
    plot_efficiency_matrix,
    plot_cop_comparison_bar,
)
import numpy as np


def run_baseline_validation():
    """Step 1: Reproduce BITZER COP values to validate the model.

    Uses calibrated η_s = 0.685 (default) which matches BITZER COP within ±2.2%.
    """
    print("=" * 70)
    print("  BASELINE VALIDATION — Reproducing BITZER/Kälte Fischer COP values")
    print("=" * 70)

    results = {}

    # Test operating points that have complete BITZER data.
    # The real CF baseline includes the flash gas IWT.
    test_points = [
        ("Summer (no PV)", OP_SUMMER_NO_PV, CO2BoosterFlashgasIWT),
        ("Transition (no PV)", OP_TRANSITION_NO_PV, CO2BoosterFlashgasIWT),
        ("WRG (no PV)", OP_WRG_NO_PV, CO2BoosterFlashgasIWT),
    ]

    for name, op, model_class in test_points:
        print(f"\n--- {name} ---")
        print(f"  BITZER COP: {op.cop_bitzer}")

        try:
            model = model_class()
            model.setup_network(iterinfo=False)
            model.set_boundary_conditions(op=op)
            model.solve()

            cop_sim = model.calculate_cop_cooling()
            results[name] = {
                "cop_bitzer": op.cop_bitzer,
                "cop_tespy": cop_sim,
                "delta_pct": (cop_sim - op.cop_bitzer) / op.cop_bitzer * 100,
            }
            print(f"  TESPy COP:  {cop_sim:.3f}")
            print(f"  Delta:      {cop_sim - op.cop_bitzer:.3f} "
                  f"({results[name]['delta_pct']:.1f}%)")

            # Generate diagrams
            res = model.get_results()
            safe_name = name.replace(" ", "_").replace("(", "").replace(")", "")
            plot_logph_diagram(res, filename=f"output/baseline_{safe_name}_logph",
                               title=f"log(p)-h: {name}")
            plot_ts_diagram(res, filename=f"output/baseline_{safe_name}_Ts",
                            title=f"T-s: {name}")

            model.print_summary()

        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = {"error": str(e)}

    return results


def run_expander_scenarios():
    """Step 2: Simulate expander variants and compare COP.

    Configurations:
        Baseline: Valve (HP) + Valve (MP)
        MD-Expander: Valve (HP) + Expander (MP) — Kälte Fischer recommended start
        HD-Expander: Expander (HP) + Valve (MP) — highest energy recovery
        Dual-Expander: Expander (HP) + Expander (MP) — maximum benefit
    """
    print("\n" + "=" * 70)
    print("  EXPANDER SCENARIOS")
    print("=" * 70)

    configs = {
        "Baseline (Valve+Valve)": {"expansion_device_hp": "valve", "expansion_device_fg": "valve"},
        "MD-Expander (vapor)": {"expansion_device_hp": "valve", "expansion_device_fg": "expander"},
        "HD-Expander": {"expansion_device_hp": "expander", "expansion_device_fg": "valve"},
        "Dual-Expander": {"expansion_device_hp": "expander", "expansion_device_fg": "expander"},
    }

    # Only use flashgas operating points without PV and with complete data.
    # Standard non-PV scenarios use the IWT baseline topology.
    test_ops = [op for op in ALL_OPERATING_POINTS
                if not op.has_parallel_compressor and op.cop_bitzer is not None]

    cop_data = {config: {} for config in configs}
    power_data = {config: {} for config in configs}

    for config_name, config_kwargs in configs.items():
        print(f"\n=== Configuration: {config_name} ===")
        for op in test_ops:
            print(f"  {op.name[:40]}...", end=" ")
            try:
                model = CO2BoosterFlashgasIWT(**config_kwargs)
                model.setup_network(iterinfo=False)
                model.set_boundary_conditions(op=op)
                model.solve()

                if not model.converged:
                    print(f"NOT CONVERGED (skipped)")
                    cop_data[config_name][op.name] = None
                    continue

                cop = model.calculate_cop_cooling()
                power = model.get_power_breakdown()
                P_comp = sum(d["P_kW"] for d in power.values() if d["type"] == "compressor")
                P_exp = sum(d["P_kW"] for d in power.values() if d["type"] == "expander")
                P_net = P_comp + P_exp

                cop_data[config_name][op.name] = cop
                power_data[config_name][op.name] = {
                    "P_comp": P_comp, "P_exp": P_exp, "P_net": P_net
                }
                print(f"COP = {cop:.3f}  P_net = {P_net:.1f} kW  W_exp = {P_exp:.1f} kW")
            except Exception as e:
                print(f"ERROR: {e}")
                cop_data[config_name][op.name] = None

    return cop_data, power_data


def print_comparison_table(cop_data, power_data):
    """Print a formatted comparison table."""
    configs = list(cop_data.keys())
    op_names = list(cop_data[configs[0]].keys())
    baseline = configs[0]

    print("\n" + "=" * 90)
    print("  RESULTS SUMMARY")
    print("=" * 90)

    # COP table
    print("\n  COP by Configuration × Operating Point:")
    header = "  Config".ljust(28)
    for op in op_names:
        header += op[:20].rjust(22)
    print(header)
    print("  " + "-" * (26 + 22 * len(op_names)))

    for config in configs:
        row = f"  {config}".ljust(28)
        for op in op_names:
            val = cop_data[config].get(op)
            if val is not None:
                row += f"{val:.3f}".rjust(22)
            else:
                row += "N/C".rjust(22)
        print(row)

    # COP improvement table
    print("\n  COP Improvement vs Baseline:")
    header = "  Config".ljust(28)
    for op in op_names:
        header += op[:20].rjust(22)
    print(header)
    print("  " + "-" * (26 + 22 * len(op_names)))

    for config in configs:
        row = f"  {config}".ljust(28)
        for op in op_names:
            val = cop_data[config].get(op)
            base = cop_data[baseline].get(op)
            if val is not None and base is not None and base > 0:
                improvement = (val - base) / base * 100
                row += f"{improvement:+.1f}%".rjust(22)
            else:
                row += "-".rjust(22)
        print(row)

    # Power recovery table
    print("\n  Power Recovery by HD/MD Expander (kW):")
    header = "  Config".ljust(28)
    for op in op_names:
        header += op[:20].rjust(22)
    print(header)
    print("  " + "-" * (26 + 22 * len(op_names)))

    for config in configs:
        row = f"  {config}".ljust(28)
        for op in op_names:
            pd = power_data[config].get(op)
            if pd is not None:
                row += f"{pd['P_exp']:.1f}".rjust(22)
            else:
                row += "-".rjust(22)
        print(row)


def main():
    """Run the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)

    # Phase 1: Validate baseline
    print("\n" + "#" * 70)
    print("  PHASE 1: BASELINE VALIDATION")
    print("#" * 70)
    baseline_results = run_baseline_validation()

    # Phase 2: Expander scenarios
    print("\n" + "#" * 70)
    print("  PHASE 2: EXPANDER COP COMPARISON")
    print("#" * 70)
    cop_data, power_data = run_expander_scenarios()

    # Phase 3: Comparison table
    print_comparison_table(cop_data, power_data)

    # Phase 4: Generate comparison plots
    # Filter out None values for plotting
    cop_clean = {}
    for config, data in cop_data.items():
        cop_clean[config] = {k: v for k, v in data.items() if v is not None}

    if cop_clean:
        plot_cop_comparison_bar(
            cop_clean,
            filename="output/cop_comparison_bar",
            title="COP by Configuration and Operating Point",
        )

        # Build efficiency matrix from clean data
        configs = list(cop_clean.keys())
        op_names = sorted(set().union(*(d.keys() for d in cop_clean.values())))
        matrix = np.array([
            [cop_clean[c].get(op, 0) for op in op_names] for c in configs
        ])
        short_labels = [n[:25].replace("(ohne Parallelverdichter)", "(no PV)") for n in op_names]
        plot_efficiency_matrix(
            matrix,
            row_labels=configs,
            col_labels=short_labels,
            filename="output/efficiency_matrix",
            title="COP Efficiency Matrix: Configurations × Operating Points",
        )

    print("\n" + "=" * 70)
    print("  DONE — Results saved to output/")
    print("=" * 70)


if __name__ == "__main__":
    main()
