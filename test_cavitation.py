"""
Simple test script to debug the cavitation visualization
"""

import sys
sys.path.append('./')

print("Testing imports...")

try:
    from HPS_regular import RegularHeatPumpStudy
    print("✓ HPS_regular imported successfully")
except Exception as e:
    print(f"✗ Error importing HPS_regular: {e}")

try:
    import numpy as np
    print("✓ numpy imported successfully")
except Exception as e:
    print(f"✗ Error importing numpy: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib imported successfully")
except Exception as e:
    print(f"✗ Error importing matplotlib: {e}")

try:
    from CoolProp.CoolProp import PropsSI as PSI
    print("✓ CoolProp imported successfully")
except Exception as e:
    print(f"✗ Error importing CoolProp: {e}")

# Test basic functionality
print("\nTesting basic functionality...")

try:
    # Test propane properties
    T_test = 20  # °C
    p_test = PSI("P", "Q", 1, "T", 273.15 + T_test, "R290") / 1e5
    print(f"✓ Propane saturation pressure at {T_test}°C: {p_test:.2f} bar")
except Exception as e:
    print(f"✗ Error calculating propane properties: {e}")

try:
    # Test creating a simple heat pump
    hp = RegularHeatPumpStudy(
        working_fluid="R290",
        Q_out=8e3,
        expansion_device="expander"
    )
    print("✓ Heat pump object created successfully")
except Exception as e:
    print(f"✗ Error creating heat pump: {e}")

print("\nBasic tests completed!")
