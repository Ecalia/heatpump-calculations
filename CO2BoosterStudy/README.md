# CO2 Booster Efficiency Study

Simulation and efficiency analysis of transcritical CO₂ booster refrigeration systems with Ecalia scroll expander integration.

## Context

Based on BITZER design data from Kälte Fischer GmbH (7 operating points for a typical REWE/EDEKA supermarket NK-stage), this study:

1. **Validates** the baseline CO₂ booster system model in TESPy against BITZER Software v7.1.2 results
2. **Quantifies** COP improvements when replacing the medium-pressure valve (MD-Ventil) with an Ecalia scroll expander
3. **Quantifies** COP improvements when replacing the high-pressure valve (HD-Ventil) with an Ecalia scroll expander
4. **Evaluates** the combined dual-expander configuration

## Key Results

### Baseline Validation (η_s = 0.685, calibrated)

| Operating Point | COP (BITZER) | COP (TESPy) | Error |
|----------------|-------------|-------------|-------|
| Summer (no PV) | 1.56 | 1.525 | -2.2% |
| Transition (no PV) | 2.97 | 2.969 | -0.0% |
| WRG mode (no PV) | 2.36 | 2.389 | +1.2% |

### Expander COP Improvement (η_exp = 0.70)

| Configuration | Summer | Transition | WRG |
|--------------|--------|------------|-----|
| Baseline (Valve+Valve) | 1.525 | 2.969 | 2.389 |
| MD-Expander (MPEV) | 1.546 (+1.4%) | 3.033 (+2.2%) | 2.433 (+1.8%) |
| HD-Expander (HPEV) | 1.855 (+21.6%) | N/C | 2.626 (+9.9%) |
| Dual-Expander | 1.883 (+23.5%) | N/C | 2.678 (+12.1%) |

### Power Recovery

| Configuration | Summer P_exp | WRG P_exp | Summer P_net saved |
|--------------|-------------|-----------|-------------------|
| MD-Expander | -0.5 kW | -0.5 kW | 0.9 kW |
| HD-Expander | -6.9 kW | -2.6 kW | 11.5 kW |
| Dual-Expander | -7.4 kW | -3.1 kW | 12.3 kW |

**Key finding**: The HD-Expander (high-pressure valve replacement) provides **14× more energy recovery** than the MD-Expander (medium-pressure valve replacement) in transcritical operation.

## Operating Points

| # | Operating Point | COP (Baseline) | Mode | High Pressure | GC Outlet |
|---|----------------|----------------|------|---------------|-----------|
| 1 | Summer (no PV) | 1.56 | Transcritical | 93.7 bar | 38 °C |
| 2 | Summer (with PV) | 1.85 | Transcritical | 93.7 bar | 38 °C |
| 3 | Transition (no PV) | 2.97 | Subcritical | — | 27 °C |
| 4 | Transition (with PV) | tbd | Subcritical | — | 27 °C |
| 5 | Winter | tbd | Subcritical | — | 38 °C |
| 6 | WRG mode (no PV) | 2.36 | Transcritical | 85 bar | 25 °C |
| 7 | WRG mode (with PV) | tbd | Transcritical | — | 25 °C |

Common parameters: Evaporation -10 °C, Superheat 6K + 4K suction line, Q₀_NK ≈ 98 kW

## Project Structure

```
CO2BoosterStudy/
├── .github/skills/       # GAIAS skills for AI-assisted development
│   ├── eng_001_tespy_simulation/
│   └── eng_002_co2_booster_design/
├── Source-Material/      # BITZER PDFs and extracted data from Kälte Fischer
├── src/
│   ├── base.py           # RefrigerationStudy base class (adapted from HeatPumpStudy)
│   ├── co2_booster.py    # CO2BoosterFlashgas + CO2BoosterParallel TESPy models
│   ├── plotting.py       # T-s, log(p)-h, efficiency matrix, COP bar chart
│   └── operating_points.py  # 7 operating point definitions from BITZER data
├── output/               # Generated plots and results
├── main.py               # Entry point for full analysis pipeline
├── requirements.txt
└── README.md
```

## Usage

```bash
pip install -r requirements.txt
python main.py
```

## Known Limitations

- **HD-Expander subcritical**: The Turbine component does not converge for subcritical HP expansion (Transition operating point). This is less critical because the HD pressure drop and recovery potential in subcritical mode are small.
- **Parallel compressor model**: `CO2BoosterParallel` is scaffolded but not yet fully validated. The IWT heat exchange constraints need refinement.
- **3 operating points missing data**: Winter, Transition (with PV), and WRG (with PV) PDFs need extraction.
- **Single compressor efficiency**: Uses a single calibrated η_s = 0.685 for all operating points. Real BITZER compressors have speed-dependent polynomial efficiency curves.

## References

- [Confluence: Transkritische CO2 Booster-Anlage](https://ecalia.atlassian.net/wiki/spaces/TECH/pages/1265172481)
- [Jira: BIZ-70](https://ecalia.atlassian.net/browse/BIZ-70)
- BITZER Software v7.1.2 — CO₂ system design tool
