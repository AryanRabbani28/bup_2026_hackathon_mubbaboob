import pytest
from app.api.models import HourEntry, BatteryData, DirectiveInterpretation
from app.optimization.optimizer import optimize_schedule

def test_optimize_schedule_basic():
    # 24 hours, constant demand, no solar, cheaper at night
    hours = []
    for i in range(24):
        tariff = 5.0 if i < 12 else 10.0
        hours.append(HourEntry(hour=i, demand_kwh=10, solar_kwh=0, tariff_bdt_per_kwh=tariff))
        
    battery = BatteryData(
        capacity_kwh=100, 
        initial_energy_kwh=50, 
        minimum_energy_kwh=10, 
        max_charge_kwh_per_hour=20, 
        max_discharge_kwh_per_hour=20
    )
    
    plan, cost = optimize_schedule(hours, battery, [])
    
    # Verify we end up at initial energy
    assert abs(plan[23].battery_energy_after_kwh - 50.0) < 1e-4
    
    # Should charge when cheap (i < 12) and discharge when expensive
    assert plan[0].battery_action in ["charge", "idle"]

def test_optimize_schedule_with_solar_reduction():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=10, tariff_bdt_per_kwh=5) for i in range(24)]
    battery = BatteryData(
        capacity_kwh=100, 
        initial_energy_kwh=50, 
        minimum_energy_kwh=10, 
        max_charge_kwh_per_hour=20, 
        max_discharge_kwh_per_hour=20
    )
    
    directives = [
        DirectiveInterpretation(
            note_index=0,
            applies=True,
            directive_type="solar_reduction",
            structured_adjustment={"hours": [12, 13], "factor": 0.5},
            explanation="test"
        )
    ]
    
    plan, cost = optimize_schedule(hours, battery, directives)
    
    # At hour 12, effective solar is 5. Demand is 10. We need 5 from grid or battery.
    # Battery can discharge. If we just look at the solar_used, it should be <= 5.
    assert plan[12].solar_used_kwh <= 5.0 + 1e-4
