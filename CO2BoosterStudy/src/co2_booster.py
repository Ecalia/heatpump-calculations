"""
CO2 Booster Flashgas System — TESPy Model

Topology (baseline without Parallel Compressor):
    NK Evaporator → NK Compressor(s) → Gas Cooler → HPEV → Flash Tank (Drum)
                                                           ├─ Liquid → MPEV (Valve) → NK Evaporator
                                                           └─ Vapor  → FGBV → NK Suction (Merge)

With Parallel Compressor variant:
    Flash Gas (vapor) → IWT (Flashgas-Gaskühler) → Parallel Compressor → HP Discharge

Expander positions:
    HD (High-Pressure):  Replaces HPEV — expansion from p_high to p_medium
    MD (Flash-Gas):      Replaces FGBV — expansion from p_medium to p_evap (vapor side!)
                         This is the alternative to a Parallel Compressor.
    Both:                HD-Expander + MD-Expander installed together

Key insight: The MD-Expander sits on the VAPOR side of the flash drum, NOT the
liquid side.  It replaces the Flash Gas Bypass Valve (FGBV) and recovers work from
expanding the flash gas from p_medium (~38 bar) down to p_evap (~26 bar).
The Parallel Compressor is the competing approach: it compresses flash gas from
p_medium UP to p_high (~94 bar).

References:
    - BITZER Software v7.1.2 CO2 system calculation
    - Confluence: Transkritische CO2 Booster-Anlage mit Parallelverdichtung
    - Kälte Fischer operating point data (Lötzsch, 26.02.2026)
"""

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
from tespy.connections import Connection
from tespy.networks import Network
from CoolProp.CoolProp import PropsSI as PSI
from typing import Optional

from .base import RefrigerationStudy
from .operating_points import OperatingPoint


class CO2BoosterFlashgas(RefrigerationStudy):
    """CO2 Booster system with flashgas bypass — baseline (no parallel compressor).

    System topology (NK only, no TK stage):
        cycle_closer → nk_compressor → gas_cooler → hpev → flash_drum
        flash_drum (liquid) → mpev (always Valve) → nk_evaporator → (merge)
        flash_drum (vapor) → fgbv/md_expander → (merge) → nk_compressor

    Expander positions:
        HD (expansion_device_hp): Replaces HPEV — p_high → p_medium
        MD (expansion_device_fg): Replaces FGBV (vapor side!) — p_medium → p_evap
    """

    def __init__(
        self,
        expansion_device_hp: str = "valve",   # "valve" or "expander"
        expansion_device_fg: str = "valve",   # "valve" or "expander" (flash gas / MD position, vapor side)
        **kwargs,
    ):
        self.expansion_device_hp = expansion_device_hp
        self.expansion_device_fg = expansion_device_fg
        super().__init__(working_fluid="CO2", **kwargs)

    def setup_components_and_connections(self):
        hp_type = Turbine if self.expansion_device_hp == "expander" else Valve
        fg_type = Turbine if self.expansion_device_fg == "expander" else Valve

        component_list = [
            # Main refrigerant cycle
            ("cycle_closer", CycleCloser),
            ("nk_compressor", Compressor),
            ("gas_cooler", SimpleHeatExchanger),
            ("hpev", hp_type),          # High-pressure expansion (valve or expander)
            ("flash_drum", DropletSeparator),  # Medium-pressure flash tank / receiver
            ("mpev", Valve),            # Medium-pressure expansion (always Valve, liquid side)
            ("nk_evaporator", SimpleHeatExchanger),
            ("fgbv", fg_type),          # Flash gas bypass: valve OR MD-expander (vapor side!)
            ("suction_merge", Merge),   # Merge of evap. gas + flash gas
        ]

        connection_list = [
            # NK compression → gas cooler → HP expansion → flash drum
            ("cycle_closer", "out1", "nk_compressor", "in1"),
            ("nk_compressor", "out1", "gas_cooler", "in1"),
            ("gas_cooler", "out1", "hpev", "in1"),
            ("hpev", "out1", "flash_drum", "in1"),

            # Flash drum liquid → MP expansion → evaporator
            ("flash_drum", "out1", "mpev", "in1"),
            ("mpev", "out1", "nk_evaporator", "in1"),
            ("nk_evaporator", "out1", "suction_merge", "in1"),

            # Flash drum gas → FGBV → merge into suction
            ("flash_drum", "out2", "fgbv", "in1"),
            ("fgbv", "out1", "suction_merge", "in2"),

            # Merge → back to compressor
            ("suction_merge", "out1", "cycle_closer", "in1"),
        ]

        self.add_components_and_connections(component_list, connection_list)

    def set_boundary_conditions(self, op: Optional[OperatingPoint] = None, **kwargs):
        """Set boundary conditions from an OperatingPoint dataclass or kwargs.

        For transcritical: set p_high and T_gc_out
        For subcritical: set T_cond and subcooling
        """
        if op is None:
            # Default: Hochsommer without PV
            from .operating_points import OP_SUMMER_NO_PV
            op = OP_SUMMER_NO_PV

        # --- Evaporator ---
        p_evap = PSI("P", "Q", 1, "T", 273.15 + op.T_evap, "CO2") / 1e5
        T_suction = op.T_evap + op.superheat_evap + op.superheat_suction

        self.comp["nk_evaporator"].set_attr(pr=0.98)
        self.conn["nk_evaporator-suction_merge"].set_attr(
            T=T_suction,
            p=p_evap,
            fluid={"CO2": 1},
        )

        # --- Compressor ---
        self.comp["nk_compressor"].set_attr(eta_s=self.compressor_efficiency)

        # --- Gas cooler / condenser ---
        self.comp["gas_cooler"].set_attr(pr=0.98)

        if op.mode == "transcritical" and op.p_high is not None:
            # Transcritical: set gas cooler pressure and outlet temperature
            self.conn["nk_compressor-gas_cooler"].set_attr(p=op.p_high)
            self.conn["gas_cooler-hpev"].set_attr(T=op.T_gc_out)
        elif op.mode == "subcritical" and op.T_cond is not None:
            # Subcritical: set condensation pressure via temperature
            p_cond = PSI("P", "Q", 0, "T", 273.15 + op.T_cond, "CO2") / 1e5
            self.conn["nk_compressor-gas_cooler"].set_attr(p=p_cond)
            if op.subcooling:
                # Use h= to avoid CoolProp flash issues during init with expanders
                h_cond_out = PSI("H", "T", 273.15 + (op.T_cond - op.subcooling),
                                 "P", p_cond * 1e5, "CO2") / 1e3
                self.conn["gas_cooler-hpev"].set_attr(h=h_cond_out)
            else:
                self.conn["gas_cooler-hpev"].set_attr(x=0)

        # --- HP expansion to medium pressure ---
        if self.expansion_device_hp == "expander":
            self.comp["hpev"].set_attr(eta_s=self.expander_efficiency)

        # Set medium pressure (flash drum / DropletSeparator pressure)
        self.conn["hpev-flash_drum"].set_attr(p=op.p_medium)

        # --- Flash drum: DropletSeparator sets x=0 on out1 and x=1 on out2 internally ---
        # Note: FGBV/MD-expander outlet pressure is determined by Merge pressure equality
        # (evaporator outlet p already sets merge pressure)

        # --- Flash gas bypass / MD-Expander (vapor side) ---
        if self.expansion_device_fg == "expander":
            self.comp["fgbv"].set_attr(eta_s=self.expander_efficiency)

        # --- Evaporator capacity (positive Q = heat absorbed by refrigerant) ---
        self.comp["nk_evaporator"].set_attr(Q=op.Q0_NK * 1e3)  # kW → W

        # --- Initial value hints for solver convergence ---
        self._set_starting_values(op)

    def _set_starting_values(self, op: OperatingPoint):
        """Provide initial enthalpy/pressure guesses for the solver."""
        p_evap = PSI("P", "Q", 1, "T", 273.15 + op.T_evap, "CO2") / 1e5
        T_suction = op.T_evap + op.superheat_evap + op.superheat_suction

        # Calculate reference state points for initial guesses
        h_suction = PSI("H", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2") / 1e3

        if op.mode == "transcritical" and op.p_high is not None:
            p_hp = op.p_high
            h_gc_out = PSI("H", "T", 273.15 + op.T_gc_out, "P", p_hp * 1e5, "CO2") / 1e3
            s_suction = PSI("S", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2")
            h_comp_s = PSI("H", "S", s_suction, "P", p_hp * 1e5, "CO2") / 1e3
            h_comp = h_suction + (h_comp_s - h_suction) / self.compressor_efficiency
        elif op.mode == "subcritical" and op.T_cond is not None:
            p_hp = PSI("P", "Q", 0, "T", 273.15 + op.T_cond, "CO2") / 1e5
            T_out = op.T_cond - (op.subcooling or 0)
            h_gc_out = PSI("H", "T", 273.15 + T_out, "P", p_hp * 1e5, "CO2") / 1e3
            s_suction = PSI("S", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2")
            h_comp_s = PSI("H", "S", s_suction, "P", p_hp * 1e5, "CO2") / 1e3
            h_comp = h_suction + (h_comp_s - h_suction) / self.compressor_efficiency
        else:
            return  # Skip if insufficient data

        h_drum_liq = PSI("H", "Q", 0, "P", op.p_medium * 1e5, "CO2") / 1e3
        h_drum_vap = PSI("H", "Q", 1, "P", op.p_medium * 1e5, "CO2") / 1e3

        # Set h0 (starting guesses) on all connections
        conn_hints = {
            "cycle_closer-nk_compressor": {"h0": h_suction, "p0": p_evap},
            "nk_compressor-gas_cooler": {"h0": h_comp, "p0": p_hp},
            "gas_cooler-hpev": {"h0": h_gc_out, "p0": p_hp * 0.98},
            "hpev-flash_drum": {"h0": h_gc_out, "p0": op.p_medium},
            "flash_drum-mpev": {"h0": h_drum_liq, "p0": op.p_medium},
            "mpev-nk_evaporator": {"h0": h_drum_liq, "p0": p_evap},
            "nk_evaporator-suction_merge": {"h0": h_suction, "p0": p_evap},
            "flash_drum-fgbv": {"h0": h_drum_vap, "p0": op.p_medium},
            "fgbv-suction_merge": {"h0": h_drum_vap, "p0": p_evap},
            "suction_merge-cycle_closer": {"h0": h_suction, "p0": p_evap},
        }
        for key, hints in conn_hints.items():
            if key in self.conn:
                self.conn[key].set_attr(**hints)

    def apply_operating_point(self, op: OperatingPoint):
        """Convenience: set BCs and solve for a specific operating point."""
        self.set_boundary_conditions(op=op)
        return self.solve()


class CO2BoosterFlashgasIWT(CO2BoosterFlashgas):
    """CO2 Booster flashgas system WITH internal heat exchanger (IWT).

    Default / BITZER reference topology:
        GC/Condenser → IWT(warm) → HPEV → Flash Drum
        Flash Drum vapor → FGBV/MD-Exp → IWT(cold) → Suction Merge

    Optional comparison topology:
        GC/Condenser → IWT(warm) → HPEV → Flash Drum
        Flash Drum vapor → IWT(cold) → FGBV/MD-Exp → Suction Merge

    `iwt_position="after_exp"` is the standard CF/BITZER baseline.
    `iwt_position="before_exp"` is available for explicit comparison studies.

    With an MD-Expander (vs FGBV valve):
    - Flash gas exits expander COLDER (less entropy generation)
    - Larger ΔT in IWT → more subcooling on HP side
    - More liquid to evaporator → more cooling capacity
    - Plus electrical work recovery from the expander
    """

    def __init__(self, iwt_position: str = "after_exp", **kwargs):
        if iwt_position not in {"after_exp", "before_exp"}:
            raise ValueError("iwt_position must be 'after_exp' or 'before_exp'.")

        self.iwt_position = iwt_position
        super().__init__(**kwargs)

    def setup_components_and_connections(self):
        hp_type = Turbine if self.expansion_device_hp == "expander" else Valve
        fg_type = Turbine if self.expansion_device_fg == "expander" else Valve

        component_list = [
            # Main NK cycle
            ("cycle_closer", CycleCloser),
            ("nk_compressor", Compressor),
            ("gas_cooler", SimpleHeatExchanger),
            ("iwt_flashgas", HeatExchanger),   # IWT: subcools HP with expanded flash gas
            ("hpev", hp_type),                 # HP expansion (valve or expander)
            ("flash_drum", DropletSeparator),
            ("mpev", Valve),                   # MP expansion (always valve, liquid side)
            ("nk_evaporator", SimpleHeatExchanger),
            ("fgbv", fg_type),                 # Flash gas: valve OR MD-expander (vapor side)
            ("suction_merge", Merge),
        ]

        connection_list = [
            # NK compression → gas cooler → IWT warm side → HP expansion → flash drum
            ("cycle_closer", "out1", "nk_compressor", "in1"),
            ("nk_compressor", "out1", "gas_cooler", "in1"),
            ("gas_cooler", "out1", "iwt_flashgas", "in1"),
            ("iwt_flashgas", "out1", "hpev", "in1"),
            ("hpev", "out1", "flash_drum", "in1"),

            # Flash drum liquid → MP expansion → evaporator
            ("flash_drum", "out1", "mpev", "in1"),
            ("mpev", "out1", "nk_evaporator", "in1"),
            ("nk_evaporator", "out1", "suction_merge", "in1"),

            # Merge → back to compressor
            ("suction_merge", "out1", "cycle_closer", "in1"),
        ]

        if self.iwt_position == "after_exp":
            connection_list[7:7] = [
                # Flash drum vapor → FGBV/MD-Exp → IWT cold side → suction merge
                ("flash_drum", "out2", "fgbv", "in1"),
                ("fgbv", "out1", "iwt_flashgas", "in2"),
                ("iwt_flashgas", "out2", "suction_merge", "in2"),
            ]
        else:
            connection_list[7:7] = [
                # Flash drum vapor → IWT cold side → FGBV/MD-Exp → suction merge
                ("flash_drum", "out2", "iwt_flashgas", "in2"),
                ("iwt_flashgas", "out2", "fgbv", "in1"),
                ("fgbv", "out1", "suction_merge", "in2"),
            ]

        self.add_components_and_connections(component_list, connection_list)

    def set_boundary_conditions(self, op: Optional[OperatingPoint] = None, **kwargs):
        if op is None:
            from .operating_points import OP_SUMMER_NO_PV
            op = OP_SUMMER_NO_PV

        # --- Evaporator ---
        p_evap = PSI("P", "Q", 1, "T", 273.15 + op.T_evap, "CO2") / 1e5
        T_suction = op.T_evap + op.superheat_evap + op.superheat_suction

        self.comp["nk_evaporator"].set_attr(pr=0.98)
        self.conn["nk_evaporator-suction_merge"].set_attr(
            T=T_suction, p=p_evap, fluid={"CO2": 1},
        )

        # --- Compressor ---
        self.comp["nk_compressor"].set_attr(eta_s=self.compressor_efficiency)

        # --- Gas cooler ---
        self.comp["gas_cooler"].set_attr(pr=0.98)

        if op.mode == "transcritical" and op.p_high is not None:
            self.conn["nk_compressor-gas_cooler"].set_attr(p=op.p_high)
            self.conn["gas_cooler-iwt_flashgas"].set_attr(T=op.T_gc_out)
        elif op.mode == "subcritical" and op.T_cond is not None:
            p_cond = PSI("P", "Q", 0, "T", 273.15 + op.T_cond, "CO2") / 1e5
            self.conn["nk_compressor-gas_cooler"].set_attr(p=p_cond)
            if op.subcooling:
                h_cond_out = PSI("H", "T", 273.15 + (op.T_cond - op.subcooling),
                                 "P", p_cond * 1e5, "CO2") / 1e3
                self.conn["gas_cooler-iwt_flashgas"].set_attr(h=h_cond_out)
            else:
                self.conn["gas_cooler-iwt_flashgas"].set_attr(x=0)

        # --- IWT ---
        self.comp["iwt_flashgas"].set_attr(pr1=0.98, pr2=0.98)

        if self.iwt_position == "after_exp":
            # BITZER-style: expand first, then warm flash gas at p_evap to the
            # suction temperature before the merge.
            T_iwt_cold_out = T_suction
            h_iwt_cold_out = PSI("H", "T", 273.15 + T_iwt_cold_out,
                                 "P", p_evap * 1e5, "CO2") / 1e3
            self.conn["iwt_flashgas-suction_merge"].set_attr(h=h_iwt_cold_out)
        else:
            # Before-exp: superheat flash gas at p_medium before the
            # valve/expander.
            T_sat_medium = PSI("T", "Q", 1, "P", op.p_medium * 1e5, "CO2") - 273.15

            # Determine warm-side inlet temperature (IWT approach constraint)
            if op.mode == "transcritical" and op.T_gc_out is not None:
                T_warm_in = op.T_gc_out
            elif op.mode == "subcritical" and op.T_cond is not None:
                T_warm_in = op.T_cond - (op.subcooling or 0)
            else:
                T_warm_in = T_sat_medium + 15  # safe fallback

            if self.expansion_device_fg == "expander":
                # Target: expander outlet matches baseline suction conditions
                # (T_suction at p_evap) → maximum subcooling, no condensation
                # risk in expander.
                # Solve: h_out = h_in - η * (h_in - h_out_s) = h_suction
                h_suction = PSI("H", "T", 273.15 + T_suction,
                                "P", p_evap * 1e5, "CO2") / 1e3
                h_iwt_cold_out = self._find_expander_inlet_h(
                    h_target_out=h_suction,
                    p_in_bar=op.p_medium,
                    p_out_bar=p_evap,
                    eta_s=self.expander_efficiency,
                )
                T_iwt_cold_out = PSI("T", "H", h_iwt_cold_out * 1e3,
                                     "P", op.p_medium * 1e5, "CO2") - 273.15
            else:
                # Valve: fixed superheat (no work recovery, isenthalpic)
                T_iwt_sh = getattr(op, "T_iwt_superheat_pv", None) or 10.0
                T_iwt_cold_out = T_sat_medium + T_iwt_sh

            # Clamp: cold outlet ≤ warm inlet − 2 K, but ≥ T_sat + 0.1 K
            T_iwt_cold_out = min(T_iwt_cold_out, T_warm_in - 2.0)
            T_iwt_cold_out = max(T_iwt_cold_out, T_sat_medium + 0.1)

            h_iwt_cold_out = PSI("H", "T", 273.15 + T_iwt_cold_out,
                                 "P", op.p_medium * 1e5, "CO2") / 1e3
            self.conn["iwt_flashgas-fgbv"].set_attr(h=h_iwt_cold_out)

        # --- HP expansion to medium pressure ---
        if self.expansion_device_hp == "expander":
            self.comp["hpev"].set_attr(eta_s=self.expander_efficiency)

        self.conn["hpev-flash_drum"].set_attr(p=op.p_medium)

        # --- Flash gas bypass / MD-Expander (vapor side) ---
        if self.expansion_device_fg == "expander":
            self.comp["fgbv"].set_attr(eta_s=self.expander_efficiency)

        # --- Evaporator capacity ---
        self.comp["nk_evaporator"].set_attr(Q=op.Q0_NK * 1e3)

        # --- Starting values ---
        self._set_starting_values(op)

    def get_canonical_state_points(self):
        """Canonical 10-point numbering consistent across booster topologies.

        Returns list of (number, connection_label, description).
        """
        if self.iwt_position == "before_exp":
            return [
                (1,  "cycle_closer-nk_compressor",  "Kompr. Eintritt"),
                (2,  "nk_compressor-gas_cooler",     "Kompr. Austritt"),
                (3,  "gas_cooler-iwt_flashgas",      "GK Austritt / IWT (warm)"),
                (4,  "iwt_flashgas-hpev",            "IWT (warm) Austritt"),
                (5,  "hpev-flash_drum",              "HD-Exp. Austritt"),
                (6,  "mpev-nk_evaporator",           "Verdampfer Eintritt"),
                (7,  "nk_evaporator-suction_merge",  "Verdampfer Austritt"),
                (8,  "flash_drum-iwt_flashgas",      "Sammler Dampf"),
                (9,  "iwt_flashgas-fgbv",            "IWT (kalt) Austritt"),
                (10, "fgbv-suction_merge",           "Exp./Ventil Austritt"),
            ]
        else:  # after_exp
            return [
                (1,  "cycle_closer-nk_compressor",  "Kompr. Eintritt"),
                (2,  "nk_compressor-gas_cooler",     "Kompr. Austritt"),
                (3,  "gas_cooler-iwt_flashgas",      "GK Austritt / IWT (warm)"),
                (4,  "iwt_flashgas-hpev",            "IWT (warm) Austritt"),
                (5,  "hpev-flash_drum",              "HD-Exp. Austritt"),
                (6,  "mpev-nk_evaporator",           "Verdampfer Eintritt"),
                (7,  "nk_evaporator-suction_merge",  "Verdampfer Austritt"),
                (8,  "flash_drum-fgbv",              "Sammler Dampf"),
                (9,  "fgbv-iwt_flashgas",            "Exp./Ventil Austritt"),
                (10, "iwt_flashgas-suction_merge",   "IWT (kalt) Austritt"),
            ]

    @staticmethod
    def _find_expander_inlet_h(h_target_out, p_in_bar, p_out_bar, eta_s):
        """Find expander inlet enthalpy [kJ/kg] so outlet reaches h_target_out.

        Uses bisection to solve:
            h_out = h_in - eta_s * (h_in - h_out_s(h_in))  ==  h_target_out
        where h_out_s = h(s(h_in, p_in), p_out).
        """
        from scipy.optimize import brentq

        def residual(h_in_kJ):
            s_in = PSI("S", "H", h_in_kJ * 1e3, "P", p_in_bar * 1e5, "CO2")
            h_out_s = PSI("H", "S", s_in, "P", p_out_bar * 1e5, "CO2") / 1e3
            h_out = h_in_kJ - eta_s * (h_in_kJ - h_out_s)
            return h_out - h_target_out

        # Search range: saturated vapor at p_in to well-superheated
        h_sat_vap = PSI("H", "Q", 1, "P", p_in_bar * 1e5, "CO2") / 1e3
        return brentq(residual, h_sat_vap, h_sat_vap + 150, xtol=0.01)

    def _set_starting_values(self, op: OperatingPoint):
        p_evap = PSI("P", "Q", 1, "T", 273.15 + op.T_evap, "CO2") / 1e5
        T_suction = op.T_evap + op.superheat_evap + op.superheat_suction
        h_suction = PSI("H", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2") / 1e3

        if op.mode == "transcritical" and op.p_high is not None:
            p_hp = op.p_high
            h_gc_out = PSI("H", "T", 273.15 + op.T_gc_out, "P", p_hp * 1e5, "CO2") / 1e3
            s_suction = PSI("S", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2")
            h_comp_s = PSI("H", "S", s_suction, "P", p_hp * 1e5, "CO2") / 1e3
            h_comp = h_suction + (h_comp_s - h_suction) / self.compressor_efficiency
        elif op.mode == "subcritical" and op.T_cond is not None:
            p_hp = PSI("P", "Q", 0, "T", 273.15 + op.T_cond, "CO2") / 1e5
            T_out = op.T_cond - (op.subcooling or 0)
            h_gc_out = PSI("H", "T", 273.15 + T_out, "P", p_hp * 1e5, "CO2") / 1e3
            s_suction = PSI("S", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2")
            h_comp_s = PSI("H", "S", s_suction, "P", p_hp * 1e5, "CO2") / 1e3
            h_comp = h_suction + (h_comp_s - h_suction) / self.compressor_efficiency
        else:
            return

        h_drum_liq = PSI("H", "Q", 0, "P", op.p_medium * 1e5, "CO2") / 1e3
        h_drum_vap = PSI("H", "Q", 1, "P", op.p_medium * 1e5, "CO2") / 1e3
        h_after_iwt = h_gc_out - 8  # ~8 kJ/kg subcooling from IWT

        conn_hints = {
            "cycle_closer-nk_compressor": {"h0": h_suction, "p0": p_evap},
            "nk_compressor-gas_cooler": {"h0": h_comp, "p0": p_hp},
            "gas_cooler-iwt_flashgas": {"h0": h_gc_out, "p0": p_hp * 0.98},
            "iwt_flashgas-hpev": {"h0": h_after_iwt, "p0": p_hp * 0.96},
            "hpev-flash_drum": {"h0": h_after_iwt, "p0": op.p_medium},
            "flash_drum-mpev": {"h0": h_drum_liq, "p0": op.p_medium},
            "mpev-nk_evaporator": {"h0": h_drum_liq, "p0": p_evap},
            "nk_evaporator-suction_merge": {"h0": h_suction, "p0": p_evap},
            "suction_merge-cycle_closer": {"h0": h_suction, "p0": p_evap},
        }

        if self.iwt_position == "after_exp":
            conn_hints.update({
                "flash_drum-fgbv": {"h0": h_drum_vap, "p0": op.p_medium},
                "fgbv-iwt_flashgas": {"h0": h_drum_vap, "p0": p_evap},
                "iwt_flashgas-suction_merge": {"h0": h_suction + 5, "p0": p_evap * 0.98},
            })
        else:
            conn_hints.update({
                "flash_drum-iwt_flashgas": {"h0": h_drum_vap, "p0": op.p_medium},
                "iwt_flashgas-fgbv": {"h0": h_drum_vap + 20, "p0": op.p_medium * 0.98},
                "fgbv-suction_merge": {"h0": h_suction, "p0": p_evap},
            })

        for key, hints in conn_hints.items():
            if key in self.conn:
                self.conn[key].set_attr(**hints)


class  CO2BoosterParallel(CO2BoosterFlashgas):
    """CO2 Booster with parallel compressor stage.

    Extends the flashgas system with a parallel compressor that handles
    the flash gas directly, compressing it to high pressure without
    mixing it into the NK suction line.

    Note: The MD-Expander position (expansion_device_fg) is NOT applicable here —
    the parallel compressor already handles the flash gas.  Only the HD-Expander
    position (expansion_device_hp) can be combined with PV.

    Additional components:
        flash_drum (gas) → iwt_flashgas → parallel_compressor → hp_merge
        gas_cooler outlet → iwt_flashgas (warm side) → hpev
    """

    def __init__(self, parallel_compressor_efficiency: float | None = None, **kwargs):
        self.parallel_compressor_efficiency = parallel_compressor_efficiency
        super().__init__(**kwargs)

    def setup_components_and_connections(self):
        hp_type = Turbine if self.expansion_device_hp == "expander" else Valve

        component_list = [
            # Main NK cycle
            ("cycle_closer", CycleCloser),
            ("nk_compressor", Compressor),
            ("hp_merge", Merge),           # Merge NK + parallel compressor discharge
            ("gas_cooler", SimpleHeatExchanger),
            ("iwt_flashgas", HeatExchanger),  # IWT: flashgas heated by GC outlet
            ("hpev", hp_type),
            ("flash_drum", DropletSeparator),
            ("mpev", Valve),               # Always Valve on liquid side
            ("nk_evaporator", SimpleHeatExchanger),

            # Parallel compressor stage
            ("parallel_compressor", Compressor),
        ]

        connection_list = [
            # NK: evaporator → compressor
            ("cycle_closer", "out1", "nk_evaporator", "in1"),
            ("nk_evaporator", "out1", "nk_compressor", "in1"),
            ("nk_compressor", "out1", "hp_merge", "in1"),

            # Parallel compressor discharge merges with NK discharge
            ("parallel_compressor", "out1", "hp_merge", "in2"),
            ("hp_merge", "out1", "gas_cooler", "in1"),

            # Gas cooler → IWT warm side → HP expansion
            ("gas_cooler", "out1", "iwt_flashgas", "in1"),
            ("iwt_flashgas", "out1", "hpev", "in1"),

            # HP expansion → flash drum
            ("hpev", "out1", "flash_drum", "in1"),

            # Drum liquid → MP expansion → evaporator
            ("flash_drum", "out1", "mpev", "in1"),
            ("mpev", "out1", "cycle_closer", "in1"),

            # Drum gas → IWT cold side → parallel compressor
            ("flash_drum", "out2", "iwt_flashgas", "in2"),
            ("iwt_flashgas", "out2", "parallel_compressor", "in1"),
        ]

        self.add_components_and_connections(component_list, connection_list)

    def set_boundary_conditions(self, op: Optional[OperatingPoint] = None, **kwargs):
        if op is None:
            from .operating_points import OP_SUMMER_WITH_PV
            op = OP_SUMMER_WITH_PV

        # --- Evaporator ---
        p_evap = PSI("P", "Q", 1, "T", 273.15 + op.T_evap, "CO2") / 1e5
        T_suction = op.T_evap + op.superheat_evap + op.superheat_suction
        # Use h= instead of T= to avoid CoolProp flash failures during init
        h_suction = PSI("H", "T", 273.15 + T_suction, "P", p_evap * 1e5, "CO2") / 1e3

        self.comp["nk_evaporator"].set_attr(pr=0.98, Q=op.Q0_NK * 1e3)
        self.conn["nk_evaporator-nk_compressor"].set_attr(
            h=h_suction, p=p_evap, fluid={"CO2": 1},
        )

        # --- NK Compressor ---
        self.comp["nk_compressor"].set_attr(eta_s=self.compressor_efficiency)

        # --- Gas cooler ---
        self.comp["gas_cooler"].set_attr(pr=0.98)

        if op.mode == "transcritical" and op.p_high is not None:
            p_hp = op.p_high
            # Use T= (not h=) so TESPy resolves h at the correct outlet
            # pressure (p_hp * pr_gc). h= at p_hp gives ~4 kJ/kg error near
            # the pseudocritical point because pr=0.98 shifts the outlet down.
            h_gc_out = PSI("H", "T", 273.15 + op.T_gc_out, "P", p_hp * 1e5, "CO2") / 1e3
            self.conn["hp_merge-gas_cooler"].set_attr(p=p_hp)
            self.conn["gas_cooler-iwt_flashgas"].set_attr(T=op.T_gc_out)
        elif op.mode == "subcritical" and op.T_cond is not None:
            p_hp = PSI("P", "Q", 0, "T", 273.15 + op.T_cond, "CO2") / 1e5
            T_out = op.T_cond - (op.subcooling or 0)
            h_gc_out = PSI("H", "T", 273.15 + T_out, "P", p_hp * 1e5, "CO2") / 1e3
            self.conn["hp_merge-gas_cooler"].set_attr(p=p_hp)
            self.conn["gas_cooler-iwt_flashgas"].set_attr(T=T_out)
        else:
            p_hp = 93.7
            h_gc_out = 311.5

        # --- IWT (internal heat exchanger for flashgas superheating) ---
        self.comp["iwt_flashgas"].set_attr(pr1=0.98, pr2=0.98)

        # --- HP expansion to medium pressure ---
        if self.expansion_device_hp == "expander":
            self.comp["hpev"].set_attr(eta_s=self.expander_efficiency)

        # --- Flash drum at medium pressure ---
        p_medium = op.p_medium_pv if op.p_medium_pv else op.p_medium
        self.conn["hpev-flash_drum"].set_attr(p=p_medium)

        # --- IWT cold side: superheat flash gas before PV compressor ---
        # Default to 10 K superheat if not specified in the OP
        T_iwt_sh = op.T_iwt_superheat_pv if op.T_iwt_superheat_pv else 10.0
        T_sat_medium = PSI("T", "Q", 1, "P", p_medium * 1e5, "CO2") - 273.15
        T_pv_suction = T_sat_medium + T_iwt_sh
        h_pv_suction = PSI("H", "T", 273.15 + T_pv_suction,
                           "P", p_medium * 1e5, "CO2") / 1e3
        self.conn["iwt_flashgas-parallel_compressor"].set_attr(h=h_pv_suction)

        # --- Parallel compressor ---
        eta_pv = self.parallel_compressor_efficiency or self.compressor_efficiency
        self.comp["parallel_compressor"].set_attr(eta_s=eta_pv)

        # --- Evaporator capacity (set above with Q) ---

        # --- Starting value hints for all connections ---
        h_drum_liq = PSI("H", "Q", 0, "P", p_medium * 1e5, "CO2") / 1e3
        h_drum_vap = PSI("H", "Q", 1, "P", p_medium * 1e5, "CO2") / 1e3

        conn_hints = {
            "cycle_closer-nk_evaporator": {"h0": h_drum_liq, "p0": p_evap},
            "nk_evaporator-nk_compressor": {"h0": h_suction, "p0": p_evap},
            "nk_compressor-hp_merge": {"h0": 535, "p0": p_hp},
            "parallel_compressor-hp_merge": {"h0": 490, "p0": p_hp},
            "hp_merge-gas_cooler": {"h0": 510, "p0": p_hp},
            "gas_cooler-iwt_flashgas": {"h0": h_gc_out, "p0": p_hp * 0.98},
            "iwt_flashgas-hpev": {"h0": h_gc_out - 5, "p0": p_hp * 0.96},
            "hpev-flash_drum": {"h0": h_gc_out - 5, "p0": p_medium},
            "flash_drum-mpev": {"h0": h_drum_liq, "p0": p_medium},
            "mpev-cycle_closer": {"h0": h_drum_liq, "p0": p_evap},
            "flash_drum-iwt_flashgas": {"h0": h_drum_vap, "p0": p_medium},
            "iwt_flashgas-parallel_compressor": {"h0": h_drum_vap + 20, "p0": p_medium * 0.98},
        }
        for key, hints in conn_hints.items():
            if key in self.conn:
                self.conn[key].set_attr(**hints)

    def get_canonical_state_points(self):
        """Canonical 10-point numbering for PV topology."""
        return [
            (1,  "nk_evaporator-nk_compressor",      "Kompr. Eintritt"),
            (2,  "nk_compressor-hp_merge",            "Kompr. Austritt"),
            (3,  "gas_cooler-iwt_flashgas",           "GK Austritt / IWT (warm)"),
            (4,  "iwt_flashgas-hpev",                 "IWT (warm) Austritt"),
            (5,  "hpev-flash_drum",                   "HD-Exp. Austritt"),
            (6,  "cycle_closer-nk_evaporator",        "Verdampfer Eintritt"),
            (7,  "nk_evaporator-nk_compressor",       "Verdampfer Austritt"),
            (8,  "flash_drum-iwt_flashgas",           "Sammler Dampf"),
            (9,  "iwt_flashgas-parallel_compressor",  "IWT (kalt) Austritt"),
            (10, "parallel_compressor-hp_merge",      "PV Austritt"),
        ]