"""
Cavitation Experiment Operating Regime Visualization
===================================================

This script creates T-S and log P-h diagrams showing the operating regime 
for propane expander cavitation experiments in heat pump cycles.

Key focus areas:
- Temperature range: -30°C to +70°C
- Pressure ranges from evaporation to condensation
- Vapor quality effects on cavitation inception
- Operating envelope for experimental design
"""

import sys
sys.path.append('./')
from HPS_regular import RegularHeatPumpStudy
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI as PSI

class CavitationExperimentVisualization:
    def __init__(self, working_fluid="R290"):
        self.working_fluid = working_fluid
        self.T_range = (-30, 70)  # °C
        self.operating_points = []
        
    def generate_operating_envelope(self):
        """Generate multiple operating points across the temperature range"""
        # Temperature points to evaluate
        T_evap_range = np.arange(-30, 15, 10)  # Evaporation temperatures
        T_cond_range = np.arange(40, 71, 10)   # Condensation temperatures
        
        operating_points = []
        
        for T_evap in T_evap_range:
            for T_cond in T_cond_range:
                if T_cond > T_evap + 20:  # Minimum 20K temperature lift
                    # Calculate pressures
                    p_evap = PSI("P", "Q", 1, "T", 273.15 + T_evap, self.working_fluid) / 1e5  # bar
                    p_cond = PSI("P", "Q", 0, "T", 273.15 + T_cond, self.working_fluid) / 1e5  # bar
                    
                    # Calculate pressure ratio
                    pressure_ratio = p_cond / p_evap
                    
                    operating_points.append({
                        'T_evap': T_evap,
                        'T_cond': T_cond,
                        'p_evap': p_evap,
                        'p_cond': p_cond,
                        'pressure_ratio': pressure_ratio,
                        'delta_p': p_cond - p_evap
                    })
        
        self.operating_points = operating_points
        return operating_points
    
    def create_representative_cycles(self):
        """Create heat pump cycles for key operating conditions"""
        # Select representative operating points
        representative_conditions = [
            {'T_evap': -20, 'T_cond': 50, 'label': 'Low Temp\n(-20°C/50°C)', 'color': '#0066CC'},
            {'T_evap': -10, 'T_cond': 60, 'label': 'Medium Temp\n(-10°C/60°C)', 'color': '#FF6600'},
            {'T_evap': 0, 'T_cond': 70, 'label': 'High Temp\n(0°C/70°C)', 'color': '#CC0000'},
        ]
        
        cycles = []
        
        for condition in representative_conditions:
            # Create heat pump with expander
            hp = RegularHeatPumpStudy(
                working_fluid=self.working_fluid,
                Q_out=8e3,
                expansion_device="expander",
                expander_efficiency=0.8
            )
            
            hp.setup_network()
            hp.set_boundary_conditions(
                T_cond=condition['T_cond'],
                T_evap=condition['T_evap']
            )
            
            try:
                hp.solve()
                cycles.append({
                    'hp': hp,
                    'condition': condition,
                    'success': True
                })
            except Exception as e:
                print(f"Failed to solve for {condition['label']}: {e}")
                cycles.append({
                    'hp': None,
                    'condition': condition,
                    'success': False
                })
        
        return cycles
    
    def plot_operating_envelope_summary(self, filename="cavitation_operating_envelope"):
        """Plot summary of operating conditions"""
        if not self.operating_points:
            self.generate_operating_envelope()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Extract data
        T_evap = [p['T_evap'] for p in self.operating_points]
        T_cond = [p['T_cond'] for p in self.operating_points]
        pressure_ratio = [p['pressure_ratio'] for p in self.operating_points]
        delta_p = [p['delta_p'] for p in self.operating_points]
        p_cond = [p['p_cond'] for p in self.operating_points]
        
        # 1. Temperature operating envelope
        scatter1 = ax1.scatter(T_evap, T_cond, c=pressure_ratio, cmap='viridis', s=60)
        ax1.set_xlabel('Evaporation Temperature (°C)')
        ax1.set_ylabel('Condensation Temperature (°C)')
        ax1.set_title('Operating Temperature Envelope')
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter1, ax=ax1, label='Pressure Ratio')
        
        # 2. Pressure vs Temperature
        scatter2 = ax2.scatter(T_cond, p_cond, c=T_evap, cmap='coolwarm', s=60)
        ax2.set_xlabel('Condensation Temperature (°C)')
        ax2.set_ylabel('Condensation Pressure (bar)')
        ax2.set_title('Pressure vs Temperature')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter2, ax=ax2, label='Evap Temp (°C)')
        
        # 3. Pressure drop across expander
        scatter3 = ax3.scatter(pressure_ratio, delta_p, c=T_cond, cmap='plasma', s=60)
        ax3.set_xlabel('Pressure Ratio (p_cond/p_evap)')
        ax3.set_ylabel('Pressure Drop Δp (bar)')
        ax3.set_title('Expander Pressure Drop')
        ax3.grid(True, alpha=0.3)
        plt.colorbar(scatter3, ax=ax3, label='Cond Temp (°C)')
        
        # 4. Cavitation risk indicator (simplified)
        # Higher pressure drops and lower temperatures increase cavitation risk
        cavitation_risk = np.array(delta_p) * (1 + np.abs(np.array(T_evap))/100)
        scatter4 = ax4.scatter(T_evap, delta_p, c=cavitation_risk, cmap='Reds', s=60)
        ax4.set_xlabel('Evaporation Temperature (°C)')
        ax4.set_ylabel('Pressure Drop Δp (bar)')
        ax4.set_title('Cavitation Risk Indicator')
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter4, ax=ax4, label='Risk Factor')
        
        plt.tight_layout()
        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.svg", bbox_inches='tight')
        plt.show()
        
        # Print summary statistics
        print("\n=== CAVITATION EXPERIMENT OPERATING ENVELOPE ===")
        print(f"Working Fluid: {self.working_fluid}")
        print(f"Temperature Range: {min(T_evap):.1f}°C to {max(T_cond):.1f}°C")
        print(f"Pressure Range: {min([p['p_evap'] for p in self.operating_points]):.1f} to {max(p_cond):.1f} bar")
        print(f"Pressure Ratio Range: {min(pressure_ratio):.1f} to {max(pressure_ratio):.1f}")
        print(f"Max Pressure Drop: {max(delta_p):.1f} bar")
        print(f"Operating Points: {len(self.operating_points)}")
    
    def plot_thermodynamic_diagrams(self, filename_base="cavitation_experiment"):
        """Create T-S and log P-h diagrams for the operating envelope"""
        cycles = self.create_representative_cycles()
        
        # Plot T-S diagram
        self._plot_ts_diagram(cycles, f"{filename_base}_ts_diagram")
        
        # Plot log P-h diagram  
        self._plot_logph_diagram(cycles, f"{filename_base}_logph_diagram")
        
        return cycles
    
    def _plot_ts_diagram(self, cycles, filename):
        """Create T-S diagram with expander operating envelope"""
        from fluprodia import FluidPropertyDiagram
        
        diagram = FluidPropertyDiagram(self.working_fluid)
        diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")
        
        # Set up the diagram
        T = np.arange(-40, 80, 5)
        Q = np.linspace(0, 1, 21)
        
        fig, ax = plt.subplots(1, figsize=(10, 8))
        
        # Calculate and set reasonable limits
        x_min, x_max = 1000, 2800  # Entropy limits for propane
        y_min, y_max = -35, 75     # Temperature limits
        
        diagram.set_isolines(T=T, Q=Q)
        diagram.calc_isolines()
        mydata = {"Q": {"values": Q}, "T": {"values": T}}
        diagram.draw_isolines(diagram_type="Ts", fig=fig, ax=ax, 
                            x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                            isoline_data=mydata)
        
        # Plot successful cycles
        for cycle_data in cycles:
            if cycle_data['success']:
                hp = cycle_data['hp']
                condition = cycle_data['condition']
                
                result_dict = hp.get_results()
                for key, data in result_dict.items():
                    result_dict[key]["datapoints"] = diagram.calc_individual_isoline(**data)
                
                # Plot the cycle
                for key in result_dict:
                    datapoints = result_dict[key]["datapoints"]
                    ax.plot(datapoints["s"], datapoints["T"], 
                           color=condition['color'], linewidth=2.5, alpha=0.8)
                    
                    # Mark the start point
                    ax.scatter(datapoints["s"][0], datapoints["T"][0], 
                             color=condition['color'], s=50, zorder=5)
                
                # Add label
                # Find a representative point for labeling
                sample_key = list(result_dict.keys())[0]
                sample_data = result_dict[sample_key]["datapoints"]
                label_x = (sample_data["s"][0] + sample_data["s"][-1]) / 2
                label_y = (sample_data["T"][0] + sample_data["T"][-1]) / 2
                
                ax.text(label_x, label_y, condition['label'], 
                       color=condition['color'], fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax.set_title(f'T-S Diagram: {self.working_fluid} Expander Operating Envelope\nfor Cavitation Experiments', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Specific Entropy s (J/(kg·K))', fontsize=12)
        ax.set_ylabel('Temperature T (°C)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add annotation about expander operation
        ax.text(0.02, 0.98, 
               'Red lines show expander\nexpansion processes\n(high → low pressure)',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.svg", bbox_inches='tight')
        plt.show()
    
    def _plot_logph_diagram(self, cycles, filename):
        """Create log P-h diagram with expander operating envelope"""
        from fluprodia import FluidPropertyDiagram
        
        diagram = FluidPropertyDiagram(self.working_fluid)
        diagram.set_unit_system(T="°C", p="bar", h="kJ/kg")
        
        # Set up the diagram
        T = np.arange(-40, 80, 5)
        Q = np.linspace(0, 1, 21)
        
        fig, ax = plt.subplots(1, figsize=(10, 8))
        
        # Calculate and set reasonable limits
        x_min, x_max = 150, 700   # Enthalpy limits for propane
        y_min, y_max = 0.5, 40    # Pressure limits (log scale)
        
        diagram.set_isolines(T=T, Q=Q)
        diagram.calc_isolines()
        mydata = {"Q": {"values": Q}, "T": {"values": T}}
        diagram.draw_isolines(diagram_type="logph", fig=fig, ax=ax,
                            x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
                            isoline_data=mydata)
        
        # Plot successful cycles
        for cycle_data in cycles:
            if cycle_data['success']:
                hp = cycle_data['hp']
                condition = cycle_data['condition']
                
                result_dict = hp.get_results()
                for key, data in result_dict.items():
                    result_dict[key]["datapoints"] = diagram.calc_individual_isoline(**data)
                
                # Plot the cycle
                for key in result_dict:
                    datapoints = result_dict[key]["datapoints"]
                    ax.plot(datapoints["h"], datapoints["p"], 
                           color=condition['color'], linewidth=2.5, alpha=0.8)
                    
                    # Mark the start point
                    ax.scatter(datapoints["h"][0], datapoints["p"][0], 
                             color=condition['color'], s=50, zorder=5)
                
                # Add label
                sample_key = list(result_dict.keys())[0]
                sample_data = result_dict[sample_key]["datapoints"]
                label_x = (sample_data["h"][0] + sample_data["h"][-1]) / 2
                label_y = (sample_data["p"][0] + sample_data["p"][-1]) / 2
                
                ax.text(label_x, label_y, condition['label'], 
                       color=condition['color'], fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax.set_title(f'log P-h Diagram: {self.working_fluid} Expander Operating Envelope\nfor Cavitation Experiments', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Specific Enthalpy h (kJ/kg)', fontsize=12)
        ax.set_ylabel('Pressure P (bar)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add annotation about cavitation
        ax.text(0.02, 0.98, 
               'Steep pressure drops\n(vertical lines) indicate\nhigh cavitation risk',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.svg", bbox_inches='tight')
        plt.show()

def main():
    """Main function to generate all cavitation experiment visualizations"""
    
    print("=== CAVITATION EXPERIMENT VISUALIZATION ===")
    print("Generating operating envelope for propane expander...")
    
    viz = CavitationExperimentVisualization(working_fluid="R290")
    
    # Generate operating envelope summary
    print("\n1. Generating operating envelope summary...")
    viz.plot_operating_envelope_summary("output/cavitation_operating_envelope")
    
    # Generate thermodynamic diagrams
    print("\n2. Generating T-S and log P-h diagrams...")
    cycles = viz.plot_thermodynamic_diagrams("output/cavitation_experiment")
    
    # Print detailed analysis
    print("\n=== CAVITATION EXPERIMENT ANALYSIS ===")
    
    for cycle_data in cycles:
        if cycle_data['success']:
            condition = cycle_data['condition']
            hp = cycle_data['hp']
            
            # Calculate some key parameters
            p_evap = PSI("P", "Q", 1, "T", 273.15 + condition['T_evap'], "R290") / 1e5
            p_cond = PSI("P", "Q", 0, "T", 273.15 + condition['T_cond'], "R290") / 1e5
            delta_p = p_cond - p_evap
            
            print(f"\n{condition['label']}:")
            print(f"  Evaporation: {condition['T_evap']:.1f}°C, {p_evap:.1f} bar")
            print(f"  Condensation: {condition['T_cond']:.1f}°C, {p_cond:.1f} bar")
            print(f"  Pressure drop: {delta_p:.1f} bar")
            print(f"  Pressure ratio: {p_cond/p_evap:.1f}")
            print(f"  COP: {hp.calculate_cop():.2f}")
    
    print("\n=== RECOMMENDATIONS FOR CAVITATION EXPERIMENTS ===")
    print("1. Focus on high pressure drop conditions (low evap temp, high cond temp)")
    print("2. Monitor vapor quality at expander inlet (target low quality for cavitation)")
    print("3. Consider variable speed operation to modify pressure ratios")
    print("4. Use high-speed visualization for cavitation inception studies")
    print("5. Measure pressure oscillations and vibrations as cavitation indicators")

if __name__ == "__main__":
    main()
