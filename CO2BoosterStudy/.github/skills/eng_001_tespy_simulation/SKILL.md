````skill
---
name: eng_001_tespy_simulation
description:  Use when building, debugging, or extending TESPy (Thermal Engineering Systems in Python) models for refrigeration cycles, heat pump systems, or booster systems. Covers: network setup with CycleCloser pattern, component wiring (Compressor, Valve, Turbine, HeatExchanger, Drum, Merge, Splitter), boundary condition strategy (which parameters to set vs. leave free), solver convergence debugging, CoolProp fluid property lookups, fluprodia diagram integration (T-s, log(p)-h), and multi-fluid / transcritical CO2 system specifics. Do NOT use for pure thermodynamic theory without TESPy code, general Python debugging, or non-TESPy simulation tools.
---

# Purpose

Guide the creation of working TESPy refrigeration/heat pump models that converge on the first or second attempt, with correct thermodynamic results.

# Prerequisites

- Python environment with `tespy>=0.7.2`, `CoolProp>=6.6.0`, `fluprodia>=2.2`
- A clear system topology (which components connect where)
- Target operating conditions (temperatures, pressures, capacities)

# Concrete Facts & Parameters

## TESPy Network Initialization Pattern

```python
from tespy.networks import Network
nw = Network(fluids=["CO2"], iterinfo=False)
nw.set_attr(p_unit="bar", T_unit="C", h_unit="kJ / kg", m_unit="kg / s")
```

- `fluids` list must contain ALL fluids in the system (even if only one)
- For CO2 transcritical: use `"CO2"` (CoolProp name), NOT `"R744"`
- For propane: use `"R290"` or `"Propane"`

## CycleCloser Pattern (CRITICAL)

Every closed refrigerant loop MUST have exactly ONE `CycleCloser` component. It is a massless, energyless connector that closes the thermodynamic cycle. Place it in the lowest-energy part of the cycle (typically between expansion device outlet and evaporator inlet, or between merge and compressor inlet).

**Common mistake:** Forgetting CycleCloser → TESPy cannot solve closed cycles.
**Common mistake:** Multiple CycleClosers in one loop → overdetermined system.

## Component Port Names

| Component | Ports | Notes |
|-----------|-------|-------|
| SimpleHeatExchanger | in1, out1 | Single-fluid HX (evaporator, gas cooler) |
| HeatExchanger | in1/out1 (hot), in2/out2 (cold) | Two-fluid HX, counter-current default |
| Compressor | in1, out1 | |
| Turbine (Expander) | in1, out1 | P is NEGATIVE (produces work) |
| Valve | in1, out1 | Isenthalpic by default |
| Drum | in1 (two-phase), out1 (liquid), out2 (vapor) | Phase separator |
| Merge | in1, in2, out1 | Mixes two streams |
| Splitter | in1, out1, out2 | Splits by mass (needs m or ratio constraint) |
| CycleCloser | in1, out1 | |

## Boundary Condition Strategy — "Degrees of Freedom"

For a closed cycle with N connections and M components:
- Each connection has 5 unknowns: T, p, h, m, fluid composition
- You must provide enough equations (component models + explicit BCs) to close the system
- Rule of thumb: set fluid composition on ONE connection, then set conditions that define the cycle

**Minimal BC set for a simple vapor-compression cycle:**
1. Evaporator outlet: `T`, `p` (or `x=1`), `fluid`
2. Compressor: `eta_s`
3. Condenser: `Q` or outlet `T`/`x=0`, `pr`
4. Expansion: nothing for Valve (isenthalpic); `eta_s` for Turbine

**DO NOT over-specify:** Setting both `T` and `p` and `h` on the same connection → overdetermined.

## Solver Debugging — Common Failures

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `ValueError: fluid property pair...` | State point in two-phase dome but trying to get T from p,h where quality needed | Add `x=1` or `x=0` constraint at that point |
| No convergence after 50 iterations | Poor initial values or contradictory BCs | Use `init_path` from a similar solved case, or relax constraints |
| `nan` in results | Pressure ratio too extreme for CoolProp | Check p values make physical sense; CO2 critical point at 73.8 bar, 31.1°C |
| Negative mass flow | Connection direction wrong | Swap in/out ports or check topology |
| `CycleCloser` residual > 1e-3 | Cycle not properly closed | Check all connections form a closed loop |
| Drum mass balance error | Missing `x=0` on liquid outlet or `x=1` on vapor outlet | Explicitly set qualities |

## CO2/R744 Specific Facts

- Critical point: T_c = 30.98°C, p_c = 73.77 bar
- Below T_c: subcritical (normal condensation possible)
- Above T_c: transcritical (gas cooler, no phase change on HP side)
- Common pressures: evaporation 26-30 bar, medium 34-43 bar, high side 45-100+ bar
- CoolProp fluid name: `"CO2"` (not `"R744"` — that works too but `"CO2"` is canonical)
- `PSI("P", "Q", 0, "T", 273.15 + T_sat, "CO2")` gives saturation pressure in Pa

## fluprodia Integration

```python
from fluprodia import FluidPropertyDiagram
diagram = FluidPropertyDiagram("CO2")
diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")
# Get plotting data from solved TESPy component:
plotting_data = component.get_plotting_data()
# Returns dict: {1: {...}, 2: {...}} for single/dual-fluid components
# Pass to: diagram.calc_individual_isoline(**data)
```

For CO2 transcritical diagrams, set T isolines from -60 to +200°C to show supercritical region clearly.

# Procedure

## Step 1: Define Topology

Draw the system on paper. Identify all components and their connections. For each closed loop, place exactly one CycleCloser.

CHECK: Does every loop have exactly one CycleCloser? IF NOT → add or remove CycleClosers.

## Step 2: Build Network

```python
nw = Network(fluids=[...], iterinfo=False)
nw.set_attr(p_unit="bar", T_unit="C", h_unit="kJ / kg", m_unit="kg / s")
```

Create all components, then all connections, then `nw.add_conns(...)`.

CHECK: Does `nw.check_network()` pass without errors? IF NOT → fix missing/duplicate connections.

## Step 3: Set Boundary Conditions

Start MINIMAL. Set only what's physically necessary:
1. Fluid composition on one connection per loop
2. One pressure anchor per pressure level (evap, medium, high)
3. Compressor/expander efficiencies
4. One capacity or mass flow constraint
5. Heat exchanger pressure ratios

CHECK: Count degrees of freedom mentally. Each connection needs 3 determined variables (p, h, and m are the main ones — fluid fixed per loop, s is derived).

## Step 4: Solve and Validate

```python
nw.solve("design")
```

If it fails, try with `iterinfo=True` to see which components have high residuals.

CHECK: Does COP match expected range? For CO2 booster NK: 1.5-3.0 depending on conditions. IF NOT → check BCs, especially pressures and temperatures.

## Step 5: Generate Diagrams

Use `component.get_plotting_data()` → `diagram.calc_individual_isoline()` → plot. Always generate both T-s and log(p)-h for visual validation that the cycle makes thermodynamic sense.

CHECK: Does the cycle shape on log(p)-h look physically correct? IF NOT → boundary conditions are wrong.

# When to Think More Abstractly

If the system topology is novel (not a standard vapor compression variant), do not force it into existing patterns. Instead, reason from first principles about mass/energy balance at each component.

If CoolProp raises errors for unusual state points (very high pressures, near critical), consider whether the operating conditions are physically realistic before debugging the code.

# Common Failure Modes & Solutions

## Over-specified System
Problem: Setting too many constraints, TESPy throws singular matrix error.
Root cause: e.g., setting T, p, AND h on same connection.
Solution: Remove redundant constraints. Only set independent properties.

## Under-specified System
Problem: TESPy converges but results are physically wrong (negative temperatures, impossible pressures).
Root cause: Not enough constraints; solver finds a mathematically valid but physically absurd solution.
Solution: Add constraints (x=0 at condenser outlet, x=1 at evaporator outlet, etc.).

## Drum Component Confusion
Problem: Drum doesn't separate phases properly.
Root cause: Missing quality constraints on outlets.
Solution: Set `x=0` on liquid outlet connection, `x=1` on vapor outlet connection.

# Related Skills

- `eng_002_co2_booster_design` — CO2-specific system architecture and operating points
- `meta_003_skill_creation` — For creating new domain-specific skills

# Skill Maintenance Notes

- Created: 2026-03-08, based on Ecalia HeatPumpStudy codebase and CO2 Booster project
- TESPy version: 0.7.2, CoolProp 6.6.0, fluprodia 2.2
- Known gap: Multi-compressor parallel configuration wiring patterns not yet documented
````
