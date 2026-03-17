````skill
---
name: eng_002_co2_booster_design
description:  Use when designing, analyzing, or simulating transcritical CO2 booster refrigeration systems for commercial refrigeration (supermarkets). Covers: flashgas bypass booster topology, parallel compressor integration, medium-pressure and high-pressure expansion valve replacement with scroll expanders, BITZER compressor selection and operating envelopes, operating point definitions (summer/transition/winter/WRG modes), sub- vs. transcritical switchover logic, and flash tank / Drum separation. Also covers interpreting BITZER Software v7.1.2 calculation outputs. Do NOT use for residential heat pumps, propane/R290 systems, or general HVAC design.
---

# Purpose

Enable accurate modeling and analysis of CO2 booster refrigeration systems to quantify the efficiency benefit of Ecalia scroll expander integration at various expansion positions.

# Prerequisites

- TESPy simulation skill (`eng_001_tespy_simulation`)
- BITZER reference data or design calculation outputs for the target system
- Understanding of which operating point is being analyzed

# Concrete Facts & Parameters

## CO2 Critical Point

- T_c = 30.98 °C, p_c = 73.77 bar
- Below ~27-28°C ambient: subcritical operation (condensation at constant T)
- Above ~32-35°C ambient: transcritical (gas cooler, no phase change)
- Transition zone: 28-35°C — system must handle switchover

## Typical Supermarket CO2 Booster Layout (NK only, no TK)

```
NK Evaporator (-10°C, ~26 bar)
  → NK Compressor(s) → discharge (~85-100 bar, ~108-119°C)
  → Gas Cooler (outlet 25-38°C depending on season)
  → HPEV (expansion to medium pressure ~38-43 bar)
  → Flash Drum / Receiver
    ├─ Liquid (x=0) → MPEV → NK Evaporator
    └─ Vapor (x=1) → FGBV → NK Suction merge
                   OR → IWT → Parallel Compressor → HP merge
```

## Pressure Levels (Kälte Fischer Reference System)

| Level | Typical Range | Design Pressure |
|-------|---------------|-----------------|
| NK Evaporation | 26 bar (-10°C sat.) | 30 bar |
| Medium / Flash Tank | 34-43 bar (3-8°C sat.) | 45 bar |
| High side (subcritical) | up to ~65 bar | 100 bar |
| High side (transcritical) | 75-100 bar | 120-160 bar |

## 7 Operating Points (Kälte Fischer, BITZER v7.1.2)

| # | Name | Mode | p_high [bar] | T_gc_out [°C] | p_med [bar] | COP | P_total [kW] |
|---|------|------|-------------|---------------|-------------|-----|-------------|
| 1 | Summer (no PV) | Trans. | 93.7 | 38 | 38 | 1.56 | 63.1 |
| 2 | Summer (with PV) | Trans. | 93.7 | 38 | 43 | 1.85 | 53.1 |
| 3 | Transition (no PV) | Sub. | — | 27 (cond.) | 38 | 2.97 | 33.2 |
| 4 | Transition (with PV) | Sub. | — | 27 (cond.) | 38 | tbd | tbd |
| 5 | Winter | Sub. | — | 38 | 38 | tbd | tbd |
| 6 | WRG (no PV) | Trans. | 85 | 25 | 38 | 2.36 | 41.7 |
| 7 | WRG (with PV) | Trans. | — | 25 | 38 | tbd | tbd |

All points: T_evap = -10°C, superheat 6K evap + 4K suction, Q0_NK ≈ 98 kW.

## Parallel Compressor Effect

- Handles flash gas separately at medium pressure → reduces NK compressor load
- Summer COP improvement: +0.29 (1.56 → 1.85)
- Transition COP improvement: +0.46 but PV barely runs (part load)
- Winter: PV cannot operate
- WRG: PV counterproductive (less flash gas, lowers discharge T → less heat recovery)
- Medium pressure INCREASES with PV (38 → 43 bar) — this is by design for PV efficiency

## Expander Integration Points

### Position A: Medium-Pressure Valve Replacement (MD-Ventil-Ersatz)
- Replaces the MPEV between flash drum liquid and evaporator
- Pressure drop: ~38-43 bar → ~26 bar
- **Recommended starting point** by Kälte Fischer
- Advantage: year-round operation, better part-load than PV
- Required pressure rating: min. 60 bar, target 80 bar

### Position B: High-Pressure Valve Replacement (HD-Ventil-Ersatz)
- Replaces the HPEV between gas cooler outlet and flash drum
- Pressure drop: 52-100 bar → 36-43 bar (much larger ΔP than Position A)
- Future target, requires pressure rating up to 130 bar
- Largest energy recovery potential in transcritical operation

### Position C: Both (Dual Expander)
- Maximum energy recovery
- More complex system, but each expander works at a different pressure ratio

## Key Metrics to Extract

For Kälte Fischer, specifically provide:
1. **Rückgewinnungsgrad** (recovery ratio) — W_expander / W_expansion_loss
2. **Flüssigkeitsanteil** (liquid fraction after expansion) — must be evaporated
3. **Regelbereich** (control range) — 0-100% target
4. **Optimale Druckdifferenz** (optimal pressure difference)

## BITZER Compressor Interpretation

- Model naming: 4JTE-10K, 4JTE-15K, 4HTE-15K, 4HTE-20K
- "4" = 4-cylinder, "J/H" = series, "TE" = transcritical, number = displacement class
- Frequency-controlled (VFD): shown as "68.0 Hz" — variable speed
- Grid-connected: shown as "--" for frequency — fixed 50 Hz
- Max operating pressure: 100/160 bar (ND/HD sides)
- Operating envelopes limited by: superheat (10-40K, VFD: 20K), motor cooling

# Procedure

## Step 1: Select Operating Point and Configuration

Choose which of the 7 operating points to simulate and which expander configuration:
- Baseline (valve + valve, no PV)
- MD-Expander (valve HP + expander MP)
- HD-Expander (expander HP + valve MP)
- Dual-Expander (expander HP + expander MP)
- Any of above with parallel compressor variant

CHECK: Is the operating point transcritical or subcritical? This determines whether to set p_high or T_cond.

## Step 2: Set System Parameters

Use the `OperatingPoint` dataclass from `operating_points.py`. Key parameters:
- T_evap, superheat values → evaporator outlet
- p_high / T_gc_out / T_cond → gas cooler boundary
- p_medium → flash drum pressure
- Q0_NK → evaporator capacity (≈98 kW)

CHECK: Are pressures above CO2 critical pressure (73.77 bar) for the HP side in transcritical mode? IF NOT → it's subcritical, use condensation temperature instead.

## Step 3: Build and Solve TESPy Model

Use `CO2BoosterFlashgas` or `CO2BoosterParallel` class. Set `expansion_device_hp` and `expansion_device_mp` to `"valve"` or `"expander"`.

CHECK: Does the COP match the BITZER reference within ±10%? If not, review boundary conditions (especially pressures and compressor efficiency).

## Step 4: Extract Results

Get COP, power breakdown, state points, and generate log(p)-h diagram. Compare against BITZER reference values. Key validations:
- COP within range
- Discharge temperature matches (±5°C)
- Flash gas mass flow in correct ballpark
- Total power consumption comparable

## Step 5: Generate Efficiency Matrix

Run all operating points × all configurations. Present as heatmap and bar chart. Calculate COP improvement percentages.

# When to Think More Abstractly

If BITZER reference data is missing for an operating point, use thermodynamic first principles to estimate expected COP range. For CO2 at these conditions, Carnot COP_cooling = T_evap / (T_gc_out - T_evap), then multiply by ~0.4-0.5 for realistic system.

If the expander introduces convergence issues (negative expansion work means two-phase Turbine), consider modeling as a Valve first with an enthalpy correction factor to approximate partial energy recovery.

# Common Failure Modes & Solutions

## Transcritical/Subcritical Confusion
Problem: Setting condensation temperature when HP is above critical pressure (or vice versa).
Root Cause: Not checking whether the operating point is sub- or transcritical.
Solution: Check T_gc_out vs. 31°C. Above → transcritical (set p_high). Below → subcritical (set T_cond).

## Flash Drum Not Separating
Problem: Drum outputs have wrong phase or mass balance error.
Root Cause: Missing quality constraints.
Solution: Always set x=0 on liquid outlet, x=1 on vapor outlet.

## Parallel Compressor Sizing
Problem: PV mass flow unrealistic.
Root Cause: Medium pressure set wrong for PV configuration (should be higher, ~43 bar vs. 38 bar).
Solution: Use p_medium_pv from the operating point data, not the base p_medium.

# Related Skills

- `eng_001_tespy_simulation` — TESPy fundamentals and debugging
- `meta_003_skill_creation` — Process for creating new GAIAS skills

# Skill Maintenance Notes

- Created: 2026-03-08, based on Kälte Fischer BITZER data and Confluence documentation
- 3 of 7 operating points still missing extracted data (Winter, Transition+PV, WRG+PV)
- Compressor efficiency values need calibration against BITZER polynomial curves
- Patent situation for IWT/flash-gas heat exchanger configurations should be checked
````
