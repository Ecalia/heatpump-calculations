"""
RefrigerationStudy base class — adapted from HeatPumpStudy for CO2-based
refrigeration and booster systems.

Key differences from HeatPumpStudy:
- Supports transcritical CO2 (R744) with gas cooler instead of condenser
- COP is calculated as Q_evap / W_total (cooling COP, not heating)
- Pressure ranges extended for CO2 (up to 130+ bar)
- p,h diagram supports supercritical region
"""

import numpy as np
import matplotlib.pyplot as plt
from tespy.components import (
    Valve,
    Compressor,
    Merge,
    Splitter,
    Turbine,
    CycleCloser,
    SimpleHeatExchanger,
    HeatExchanger,
    DropletSeparator,
)
from tespy.components.component import Component
from tespy.connections import Connection
from tespy.networks import Network
from CoolProp.CoolProp import PropsSI as PSI
from typing import Dict, Optional, Tuple
from itertools import chain


def alternate(*lists):
    """Interleave multiple lists element-wise."""
    return list(chain.from_iterable(zip(*lists)))


class RefrigerationStudy:
    """Base class for TESPy-based refrigeration system simulations."""

    def __init__(
        self,
        working_fluid: str = "CO2",
        compressor_efficiency: float = 0.685,
        expander_efficiency: float = 0.70,
    ):
        self.working_fluid = working_fluid
        self.compressor_efficiency = compressor_efficiency
        self.expander_efficiency = expander_efficiency
        self.comp: Dict[str, Component] = {}
        self.conn: Dict[str, Connection] = {}
        self.network: Optional[Network] = None

    def setup_network(self, iterinfo: bool = False) -> "RefrigerationStudy":
        """Initialize the TESPy network, build topology, set BCs."""
        self.comp = {}
        self.conn = {}
        self.network = Network(
            fluids=[self.working_fluid], iterinfo=iterinfo,
            T_unit="C", p_unit="bar", h_unit="kJ / kg",
            m_unit="kg / s", v_unit="l / s",
        )
        self.setup_components_and_connections()
        self.network.add_conns(*list(self.conn.values()))
        return self

    # --- Override in subclasses ---

    def setup_components_and_connections(self):
        raise NotImplementedError("Implement in subclass")

    def set_boundary_conditions(self, **kwargs):
        raise NotImplementedError("Implement in subclass")

    # --- Component / connection helpers ---

    def add_components_and_connections(self, component_list, connection_list):
        """Add components and connections from definition lists.

        component_list: [(name, ComponentClass), ...]
        connection_list: [(comp1_name, out_port, comp2_name, in_port), ...]
        """
        for name, comp_class in component_list:
            self.comp[name] = comp_class(name)

        for comp1, out_port, comp2, in_port in connection_list:
            label = f"{comp1}-{comp2}"
            self.conn[label] = Connection(
                self.comp[comp1], out_port,
                self.comp[comp2], in_port,
                label=label,
            )

    def repeat_comp(self, name: str, comp_type: type, N: int):
        """Generate N component tuples: [(name_1, type), (name_2, type), ...]"""
        return [(f"{name}_{i+1}", comp_type) for i in range(N)]

    def repeat_conn(
        self, out_label: str, out_port: str,
        in_label: str, in_port: str,
        out_id_start: int = 1, in_id_start: int = 1, N: int = 1,
    ):
        """Generate N connection tuples with incrementing indices."""
        return [
            (f"{out_label}_{i + out_id_start}", out_port,
             f"{in_label}_{i + in_id_start}", in_port)
            for i in range(N)
        ]

    # --- Solving ---

    def solve(self, mode: str = "design", **kwargs) -> "RefrigerationStudy":
        if self.network is None:
            raise ValueError("Network not set up. Call setup_network() first.")
        self.network.solve(mode=mode, **kwargs)
        return self

    @property
    def converged(self) -> bool:
        """Check if the last solve converged properly."""
        if self.network is None:
            return False
        return (
            not getattr(self.network, "lin_dep", True)
            and getattr(self.network, "converged", False)
        )

    # --- Results extraction ---

    def calculate_cop_cooling(self) -> float:
        """COP for cooling: Q_evap / W_compressors (positive value)."""
        Q_evap = 0.0
        for comp in self.comp.values():
            if isinstance(comp, SimpleHeatExchanger) and "evaporator" in comp.label:
                Q_evap += abs(comp.Q.val)
        W = sum(
            comp.P.val for comp in self.comp.values()
            if isinstance(comp, Compressor)
        )
        W_expander = sum(
            comp.P.val for comp in self.comp.values()
            if isinstance(comp, Turbine)
        )
        # Expander power is negative (produces work), so W_net = W_comp + W_exp
        W_net = W + W_expander
        if W_net == 0:
            return float("inf")
        return Q_evap / W_net

    def calculate_cop_eer(self) -> float:
        """EER = Q_evap / P_total (same as cooling COP for this system)."""
        return self.calculate_cop_cooling()

    def get_power_breakdown(self) -> dict:
        """Return power consumption/production for each compressor and expander.

        All values in kW (TESPy stores P in W).
        """
        result = {}
        for comp in self.comp.values():
            if isinstance(comp, (Compressor, Turbine)):
                result[comp.label] = {
                    "P_kW": comp.P.val / 1e3,
                    "type": "compressor" if isinstance(comp, Compressor) else "expander",
                }
        return result

    def get_state_points(self) -> dict:
        """Return T, p, h, s, x for all connections."""
        points = {}
        for label, conn in self.conn.items():
            points[label] = {
                "T": conn.T.val,        # °C
                "p": conn.p.val,        # bar
                "h": conn.h.val,        # kJ/kg
                "s": conn.s.val,        # kJ/(kg·K)
                "x": conn.x.val,        # vapor quality
                "m": conn.m.val,        # kg/s
            }
        return points

    def get_results(self) -> dict:
        """Get plotting data for all components (for fluprodia diagrams)."""
        results = {}
        for comp in self.comp.values():
            if isinstance(comp, (HeatExchanger, Merge)):
                plotting_data = comp.get_plotting_data()
                if plotting_data is not None:
                    for idx in plotting_data:
                        if plotting_data[idx] is not None:
                            results[f"{comp.label}_{idx}"] = plotting_data[idx]
            elif not isinstance(comp, (CycleCloser, Splitter, DropletSeparator)):
                plotting_data = comp.get_plotting_data()
                if plotting_data is not None:
                    for idx in plotting_data:
                        if plotting_data[idx] is not None:
                            results[f"{comp.label}" if idx == 1 else f"{comp.label}_{idx}"] = plotting_data[idx]
        return results

    # --- Printing ---

    def print_summary(self):
        """Print a summary of the simulation results."""
        print(f"\n{'='*60}")
        print(f"  {self.__class__.__name__} — {self.working_fluid}")
        print(f"{'='*60}")
        print(f"  COP (cooling): {self.calculate_cop_cooling():.3f}")
        print(f"\n  Power breakdown:")
        for name, data in self.get_power_breakdown().items():
            sign = "+" if data["P_kW"] < 0 else "-"
            print(f"    {name}: {abs(data['P_kW']):.2f} kW ({data['type']}) [{sign}]")
        P_net = sum(d["P_kW"] for d in self.get_power_breakdown().values())
        print(f"    Net power: {P_net:.2f} kW")
        print(f"\n  Key state points:")
        for label, state in self.get_state_points().items():
            print(f"    {label:40s}  T={state['T']:7.1f}°C  p={state['p']:6.1f}bar  "
                  f"h={state['h']:7.1f}kJ/kg  m={state['m']:.4f}kg/s")
        print(f"{'='*60}\n")
