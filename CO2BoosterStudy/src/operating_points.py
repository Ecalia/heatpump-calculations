"""
Operating point definitions extracted from BITZER Software v7.1.2 calculations
provided by Kälte Fischer GmbH (Benaja Lötzsch, 26.02.2026).

All points: NK-Stufe only (TK deliberately excluded for clean COP comparison).
Q0_NK held constant at ~98 kW across all points for comparability.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OperatingPoint:
    """A single BITZER design operating point for the CO2 booster system."""
    name: str
    mode: str  # "transcritical" or "subcritical"
    has_parallel_compressor: bool

    # Evaporator
    T_evap: float = -10.0          # °C, evaporation temperature
    superheat_evap: float = 6.0    # K, evaporator superheat
    superheat_suction: float = 4.0 # K, suction line superheat
    Q0_NK: float = 98.0            # kW, NK evaporator capacity (approximate)

    # High pressure side
    p_high: Optional[float] = None  # bar(a), gas cooler / condenser pressure
    T_gc_out: Optional[float] = None  # °C, gas cooler outlet temperature
    T_cond: Optional[float] = None    # °C, condensation temperature (subcritical only)
    subcooling: Optional[float] = None  # K, liquid subcooling (subcritical only)

    # Medium pressure
    p_medium: float = 38.0         # bar(a), intermediate pressure
    T_medium: float = 3.3          # °C, saturation at medium pressure

    # Parallel compressor
    p_medium_pv: Optional[float] = None  # bar(a), medium pressure with PV (can differ)
    T_iwt_superheat_pv: Optional[float] = None  # K, IWT superheat for parallel stage

    # Results from BITZER
    cop_bitzer: Optional[float] = None  # COP/EER from BITZER calculation
    P_total: Optional[float] = None     # kW, total power consumption
    Q_gc: Optional[float] = None        # kW, gas cooler / condenser capacity
    m_total: Optional[float] = None     # kg/h, total refrigerant mass flow
    m_flashgas: Optional[float] = None  # kg/h, flash gas mass flow
    T_discharge: Optional[float] = None # °C, discharge temperature (uncooled)
    p_high_opt: Optional[float] = None  # bar(a), optimal high pressure

    # Compressor configuration
    compressors_nk: str = ""       # e.g. "2x 4JTE-15K + 1x 4JTE-10K"
    compressor_pv: str = ""        # e.g. "1x 4JTE-15K"

    # Additional notes
    notes: str = ""


# =============================================================================
# Operating Points from BITZER/Kälte Fischer data
# =============================================================================

OP_SUMMER_NO_PV = OperatingPoint(
    name="Hochsommer (ohne Parallelverdichter)",
    mode="transcritical",
    has_parallel_compressor=False,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.7,
    p_high=93.7,
    T_gc_out=38.0,
    p_medium=38.0,
    T_medium=3.3,
    cop_bitzer=1.56,
    P_total=63.1,
    Q_gc=164.0,
    m_flashgas=1130,
    T_discharge=118.7,
    p_high_opt=93.7,
    compressors_nk="1x 4HTE-20K (70Hz VFD) + 3x 4HTE-15K",
    notes="Highest load, worst COP. 4 compressors needed.",
)

OP_SUMMER_WITH_PV = OperatingPoint(
    name="Hochsommer (mit Parallelverdichter)",
    mode="transcritical",
    has_parallel_compressor=True,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.2,
    p_high=93.7,
    T_gc_out=38.0,
    p_medium=43.0,       # Higher medium pressure with PV
    T_medium=8.2,
    p_medium_pv=43.0,
    T_iwt_superheat_pv=10.0,
    cop_bitzer=1.85,
    P_total=53.1,         # NK: 38.4 + PV: 14.68
    Q_gc=156.9,
    m_flashgas=1101,      # PV mass flow
    T_discharge=119.5,
    p_high_opt=93.7,
    compressors_nk="1x 4JTE-15K (68Hz VFD) + 1x 4JTE-10K",
    compressor_pv="1x 4JTE-15K (62Hz VFD)",
    notes="COP improvement of 0.29 vs. without PV. Target for expander.",
)

OP_TRANSITION_NO_PV = OperatingPoint(
    name="Übergangsjahreszeit (ohne Parallelverdichter)",
    mode="subcritical",
    has_parallel_compressor=False,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.6,
    T_cond=27.0,
    subcooling=3.0,
    p_medium=38.0,
    T_medium=3.3,
    cop_bitzer=2.97,
    P_total=33.2,
    Q_gc=134.1,           # Actually condenser capacity here
    m_flashgas=480,
    T_discharge=84.2,
    compressors_nk="1x 4HTE-20K (53Hz VFD) + 1x 4HTE-15K",
    notes="Subcritical operation. PV improvement 0.46 but PV barely runs (part load).",
)

OP_TRANSITION_WITH_PV = OperatingPoint(
    name="Übergangsjahreszeit (mit Parallelverdichter)",
    mode="subcritical",
    has_parallel_compressor=True,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.6,
    T_cond=27.0,
    subcooling=3.0,
    p_medium=43.0,        # Higher medium pressure with PV (vs. 38 bar without)
    T_medium=8.2,
    p_medium_pv=43.0,
    T_iwt_superheat_pv=10.0,
    cop_bitzer=3.43,
    P_total=28.8,          # NK: 27.1 + PV: 1.66
    Q_gc=118.8,            # Condenser capacity
    m_total=1780,          # kg/h, condenser mass flow
    m_flashgas=187,        # kg/h, PV mass flow (flash gas compressed by PV)
    T_discharge=85.0,
    compressors_nk="1x 4JTE-15K (56Hz VFD) + 2x 4JTE-10K",
    compressor_pv="1x 2MTE-5K (30Hz VFD)",
    notes="Subcritical PV operation. PV barely runs (1.66 kW, 30Hz). "
          "COP improvement 0.46 vs. without PV (3.43 vs. 2.97).",
)

OP_WINTER = OperatingPoint(
    name="Winterbetrieb",
    mode="subcritical",
    has_parallel_compressor=False,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.9,
    T_cond=17.0,           # Winter condensation temperature
    subcooling=3.0,
    p_medium=38.0,
    T_medium=3.3,
    cop_bitzer=4.54,
    P_total=21.8,
    Q_gc=122.9,            # Condenser capacity
    m_total=1708,          # kg/h, total mass flow
    m_flashgas=196.1,      # kg/h, minimal flash gas in winter
    T_discharge=63.3,      # °C, low discharge temp (subcritical low ΔP)
    compressors_nk="1x 4HTE-20K (27Hz VFD) + 2x 4HTE-15K",
    notes="Winter subcritical. Best COP (4.54). Only 196 kg/h flash gas. "
          "4HTE-20K runs at min speed (27Hz). PV cannot operate.",
)

OP_WRG_NO_PV = OperatingPoint(
    name="WRG-Modul (ohne Parallelverdichter)",
    mode="transcritical",
    has_parallel_compressor=False,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.2,
    p_high=85.0,
    T_gc_out=25.0,
    p_medium=38.0,
    T_medium=3.3,
    cop_bitzer=2.36,
    P_total=41.7,
    Q_gc=142.1,
    m_flashgas=421,
    T_discharge=108.2,
    p_high_opt=75.0,
    compressors_nk="1x 4HTE-20K (57Hz VFD) + 1x 4HTE-15K",
    notes="Good operating point for expander: long annual runtime, decent flash gas amount. "
          "GC outlet 25°C (heat recovery). Optimal HP would be 75 bar but set to 85.",
)

OP_WRG_WITH_PV = OperatingPoint(
    name="WRG-Modus (mit Parallelverdichter)",
    mode="transcritical",
    has_parallel_compressor=True,
    T_evap=-10.0,
    superheat_evap=6.0,
    superheat_suction=4.0,
    Q0_NK=98.9,
    p_high=85.0,
    T_gc_out=25.0,
    p_medium=38.0,
    T_medium=3.3,
    p_medium_pv=38.0,
    T_iwt_superheat_pv=10.0,
    cop_bitzer=2.48,
    P_total=39.8,          # NK: 33.4 + PV: 6.40
    Q_gc=141.8,
    m_total=1940,          # kg/h, gas cooler mass flow (NK 1511 + PV 429)
    m_flashgas=429,        # kg/h, PV mass flow (flash gas)
    T_discharge=109.4,
    p_high_opt=75.0,
    compressors_nk="1x 4KTE-12K (58Hz VFD) + 2x 4JTE-10K",
    compressor_pv="1x 2KTE-7K (57Hz VFD)",
    notes="WRG transcritical with PV. COP 2.48 vs. 2.36 without PV (+0.12). "
          "PV counterproductive for heat recovery (lowers discharge temp from 108 to 94°C).",
)

# Ordered list of all operating points
ALL_OPERATING_POINTS = [
    OP_SUMMER_NO_PV,
    OP_SUMMER_WITH_PV,
    OP_TRANSITION_NO_PV,
    OP_TRANSITION_WITH_PV,
    OP_WINTER,
    OP_WRG_NO_PV,
    OP_WRG_WITH_PV,
]

# Expander requirements from Kälte Fischer (Lötzsch)
EXPANDER_REQUIREMENTS = {
    "md_valve": {
        "description": "Mitteldruckventil-Ersatz (sinnvoller Einstieg)",
        "T_evap_range": (-15, -3),           # °C
        "p_medium_range": (36, 43),          # bar
        "pressure_rating_min": 60,           # bar
        "pressure_rating_target": 80,        # bar
        "controllability": "0-100%, parallel valve or 2nd expander possible",
    },
    "hd_valve": {
        "description": "Hochdruckventil-Ersatz (zukünftig)",
        "p_high_range": (52, 100),           # bar (annual range)
        "p_medium_range": (36, 43),          # bar
        "pressure_rating_future": 130,       # bar
        "controllability": "0-100%, parallel valve or 2nd expander possible",
    },
}

# Information requested by Kälte Fischer about the expander
INFO_REQUESTED = [
    "Rückgewinnungsgrad (recovery ratio)",
    "Flüssigkeitsanteil nach Expansion (liquid fraction, must be evaporated)",
    "Regelbereich (control range)",
    "Optimale Druckdifferenz (optimal pressure difference)",
]
