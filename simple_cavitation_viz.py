"""
Simple Cavitation Experiment Visualization
==========================================

Creates basic visualizations for propane expander cavitation experiments
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

# Import the heat pump study modules
sys.path.append('./')
from HPS_regular import RegularHeatPumpStudy
from CoolProp.CoolProp import PropsSI as PSI

def create_simple_visualization():
    """Create a simple visualization showing operating conditions"""
    
    print("Creating simple cavitation experiment visualization...")
    
    # Define operating conditions
    working_fluid = "R290"  # Propane
    
    # Temperature ranges for experiments
    T_evap_range = np.arange(-30, 15, 10)  # -30°C to 10°C
    T_cond_range = np.arange(40, 71, 10)   # 40°C to 70°C
    
    # Calculate pressure ranges
    print(f"Working fluid: {working_fluid}")
    print("Temperature and pressure ranges:")
    
    operating_points = []
    
    for T_evap in T_evap_range:
        for T_cond in T_cond_range:
            if T_cond > T_evap + 20:  # Minimum 20K temperature lift
                try:
                    # Calculate saturation pressures
                    p_evap = PSI("P", "Q", 1, "T", 273.15 + T_evap, working_fluid) / 1e5  # bar
                    p_cond = PSI("P", "Q", 0, "T", 273.15 + T_cond, working_fluid) / 1e5  # bar
                    
                    pressure_ratio = p_cond / p_evap
                    delta_p = p_cond - p_evap
                    
                    operating_points.append({
                        'T_evap': T_evap,
                        'T_cond': T_cond,
                        'p_evap': p_evap,
                        'p_cond': p_cond,
                        'pressure_ratio': pressure_ratio,
                        'delta_p': delta_p
                    })
                    
                    print(f"  T_evap={T_evap:3.0f}°C, T_cond={T_cond:2.0f}°C → p_evap={p_evap:4.1f} bar, p_cond={p_cond:4.1f} bar, Δp={delta_p:4.1f} bar")
                    
                except Exception as e:
                    print(f"  Error for T_evap={T_evap}°C, T_cond={T_cond}°C: {e}")
    
    # Create visualization
    if operating_points:
        # Extract data for plotting
        T_evap = [p['T_evap'] for p in operating_points]
        T_cond = [p['T_cond'] for p in operating_points]
        delta_p = [p['delta_p'] for p in operating_points]
        pressure_ratio = [p['pressure_ratio'] for p in operating_points]
        
        # Create plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Operating envelope
        scatter1 = ax1.scatter(T_evap, T_cond, c=pressure_ratio, cmap='viridis', s=60)
        ax1.set_xlabel('Evaporation Temperature (°C)')
        ax1.set_ylabel('Condensation Temperature (°C)')
        ax1.set_title('Operating Temperature Envelope')
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter1, ax=ax1, label='Pressure Ratio')
        
        # 2. Pressure vs Temperature
        p_cond = [p['p_cond'] for p in operating_points]
        scatter2 = ax2.scatter(T_cond, p_cond, c=T_evap, cmap='coolwarm', s=60)
        ax2.set_xlabel('Condensation Temperature (°C)')
        ax2.set_ylabel('Condensation Pressure (bar)')
        ax2.set_title('Pressure vs Temperature')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=ax2, label='Evap Temp (°C)')
        
        # 3. Pressure drop analysis
        scatter3 = ax3.scatter(pressure_ratio, delta_p, c=T_cond, cmap='plasma', s=60)
        ax3.set_xlabel('Pressure Ratio (p_cond/p_evap)')
        ax3.set_ylabel('Pressure Drop Δp (bar)')
        ax3.set_title('Expander Pressure Drop')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter3, ax=ax3, label='Cond Temp (°C)')
        
        # 4. Cavitation risk indicator
        cavitation_risk = np.array(delta_p) * (1 + np.abs(np.array(T_evap))/100)
        scatter4 = ax4.scatter(T_evap, delta_p, c=cavitation_risk, cmap='Reds', s=60)
        ax4.set_xlabel('Evaporation Temperature (°C)')
        ax4.set_ylabel('Pressure Drop Δp (bar)')
        ax4.set_title('Cavitation Risk Indicator')
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter4, ax=ax4, label='Risk Factor')
        
        plt.suptitle('Propane Expander Cavitation Experiment Operating Envelope', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save plots
        plt.savefig('output/simple_cavitation_envelope.png', dpi=300, bbox_inches='tight')
        plt.savefig('output/simple_cavitation_envelope.svg', bbox_inches='tight')
        print("\\nPlots saved to output/simple_cavitation_envelope.png and .svg")
        
        # Show plot
        plt.show()
        
        # Print summary
        print("\\n=== OPERATING ENVELOPE SUMMARY ===")
        print(f"Total operating points: {len(operating_points)}")
        print(f"Temperature range: {min(T_evap):.0f}°C to {max(T_cond):.0f}°C")
        print(f"Pressure range: {min([p['p_evap'] for p in operating_points]):.1f} to {max([p['p_cond'] for p in operating_points]):.1f} bar")
        print(f"Max pressure drop: {max(delta_p):.1f} bar")
        print(f"Max pressure ratio: {max(pressure_ratio):.1f}")
        
        return operating_points
    else:
        print("No valid operating points found!")
        return []

def create_simple_cycle_diagram():
    """Create a simple T-S diagram for one representative cycle"""
    
    print("\\nCreating representative cycle diagram...")
    
    try:
        # Create heat pump with expander
        hp = RegularHeatPumpStudy(
            working_fluid="R290",
            Q_out=8e3,
            expansion_device="expander",
            expander_efficiency=0.8
        )
        
        hp.setup_network()
        hp.set_boundary_conditions(T_cond=60, T_evap=-10)
        hp.solve()
        
        # Try to create a basic T-S diagram
        hp.plot_ts_diag("output/simple_cavitation_ts", x_min=1200, x_max=2600, y_min=-35, y_max=80)
        hp.plot_logph_diag("output/simple_cavitation_logph", x_min=200, x_max=700, y_min=1, y_max=35)
        
        print("T-S and log P-h diagrams saved!")
        
        # Calculate some key metrics
        cop = hp.calculate_cop()
        print(f"\\nCycle performance:")
        print(f"COP: {cop:.2f}")
        
        return hp
        
    except Exception as e:
        print(f"Error creating cycle diagram: {e}")
        return None

if __name__ == "__main__":
    print("=== SIMPLE CAVITATION EXPERIMENT VISUALIZATION ===")
    
    # Create operating envelope
    operating_points = create_simple_visualization()
    
    # Create cycle diagram
    hp = create_simple_cycle_diagram()
    
    print("\\n=== RECOMMENDATIONS FOR CAVITATION EXPERIMENTS ===")
    print("1. Focus on high pressure drop conditions (low evap temp, high cond temp)")
    print("2. Monitor vapor quality at expander inlet (target low quality for cavitation)")
    print("3. Use high-speed visualization for cavitation inception studies")
    print("4. Consider variable expander geometry/speed to modify pressure ratios")
    print("5. Measure pressure oscillations and vibrations as cavitation indicators")
    print("\\nVisualization complete!")
