import sys
sys.path.append('../')
from HPS_regular import RegularHeatPumpStudy
from CoolProp.CoolProp import PropsSI as PSI

class HeatPumpStudy(RegularHeatPumpStudy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def set_boundary_conditions(self, T_cond=62, T_evap=11, T_overheating=5, T_subcooling=5):

        p_cond = PSI("P", "Q", 0, "T", 273.15 + T_cond, self.working_fluid) / 1e5
        p_evap = PSI("P", "Q", 1, "T", 273.15 + T_evap, self.working_fluid) / 1e5
        

        
        self.comp["evaporator"].set_attr(pr=0.98)
        self.conn["evaporator-compressor"].set_attr(p=p_evap, T=T_evap+T_overheating, fluid={self.working_fluid: 1})
        self.comp["compressor"].set_attr(eta_s=self.compressor_efficiency)
        self.comp["condenser"].set_attr(pr=0.98, Q=-self.Q_out)
        self.conn["condenser-expansionValve"].set_attr(T=T_cond-T_subcooling, p=p_cond)
        if self.expansion_device == "expander":
            self.conn["expansionValve-expander"].set_attr(x=0.01)            
            self.comp["expander"].set_attr(eta_s=self.expander_efficiency)

        return self