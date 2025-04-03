from HeatPumpStudy import HeatPumpStudy
from tespy.components import (Valve, Sink, Source, Pump, Compressor, Condenser, Turbine, CycleCloser, SimpleHeatExchanger)
from tespy.connections import Connection
from CoolProp.CoolProp import PropsSI as PSI

class AirConditionerStudy(HeatPumpStudy):
    def __init__(self, Q_in,**kwargs):
        self.Q_in = Q_in

        super().__init__(**kwargs)


    def setup_components_and_connections(self):
        expansion_type = Valve
        if self.expansion_device == "expander":
            expansion_type = Turbine
        elif self.expansion_device != "expansionValve":
            raise ValueError("expansion_device must be either 'expansionValve' or 'expander'")
    
        component_list = [
            ("evaporator", SimpleHeatExchanger),
            ("compressor", Compressor),
            ("condenser", SimpleHeatExchanger),
            ("expansionValve", Valve)]
        if self.expansion_device == "expander":
            component_list.append(("expander", Turbine))
        component_list.append(("cycle_closer", CycleCloser))
        
        
        

        connection_list = [
            ("cycle_closer", "out1", "evaporator", "in1"),
            ("evaporator", "out1", "compressor", "in1"),
            ("compressor", "out1", "condenser", "in1"),
            ("condenser", "out1", "expansionValve", "in1")]
        
        if self.expansion_device == "expander":
            connection_list.append(("expansionValve", "out1", "expander", "in1"))
    
        connection_list.append((self.expansion_device, "out1", "cycle_closer", "in1"))
        
        self.add_components_and_connections(component_list, connection_list)
        #self.add_condenser_cooling()# need to change condenser to Condenser when used and SimpleHeatExchanger when not used


   
    def calculate_cop(self, consumer="evaporator"):
        Q = abs(self.comp[consumer].Q.val)
        W = sum(
            comp.P.val
            for comp in self.comp.values()
            if isinstance(comp, (Compressor, Turbine))
        )
        return Q / W

    def set_boundary_conditions(self, T_cond=80, T_evap=20, T_overheating=5, T_subcooling=5):

        p_cond = PSI("P", "Q", 0, "T", 273.15 + T_cond, self.working_fluid) / 1e5
        p_evap = PSI("P", "Q", 1, "T", 273.15 + T_evap, self.working_fluid) / 1e5
        

        self.comp["evaporator"].set_attr(pr=0.98, Q=self.Q_in)
        self.conn["evaporator-compressor"].set_attr(p=p_evap, T=T_evap+T_overheating, fluid={self.working_fluid: 1})
        self.comp["compressor"].set_attr(eta_s=self.compressor_efficiency)
        self.comp["condenser"].set_attr(pr=0.98)
        self.conn["condenser-expansionValve"].set_attr(T=T_cond-T_subcooling, p=p_cond)
        if self.expansion_device == "expander":
            self.conn["expansionValve-expander"].set_attr(x=0.01)            
            self.comp["expander"].set_attr(eta_s=self.expander_efficiency)

        return self