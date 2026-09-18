import pytest
from app.api.models import HourEntry, BatteryData, HourlyPlanEntry, DirectiveInterpretation
from app.validation.schedule_validator import validate_schedule, ScheduleValidationError

def test_validate_schedule_valid():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=0, tariff_bdt_per_kwh=5) for i in range(24)]
    battery = BatteryData(capacity_kwh=100, initial_energy_kwh=50, minimum_energy_kwh=10, max_charge_kwh_per_hour=20, max_discharge_kwh_per_hour=20)
    
    plan = []
    for i in range(24):
        plan.append(HourlyPlanEntry(
            hour=i,
            grid_kwh=10,
            solar_used_kwh=0,
            battery_action="idle",
            battery_kwh=0,
            battery_energy_after_kwh=50
        ))
        
    tot_grid, tot_cost, peak = validate_schedule(hours, battery, [], plan)
    assert abs(tot_grid - 240) < 1e-4
    assert abs(tot_cost - 1200) < 1e-4

def test_validate_schedule_invalid_balance():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=0, tariff_bdt_per_kwh=5) for i in range(24)]
    battery = BatteryData(capacity_kwh=100, initial_energy_kwh=50, minimum_energy_kwh=10, max_charge_kwh_per_hour=20, max_discharge_kwh_per_hour=20)
    
    plan = []
    for i in range(24):
        plan.append(HourlyPlanEntry(
            hour=i,
            grid_kwh=5, # Invalid: demand is 10
            solar_used_kwh=0,
            battery_action="idle",
            battery_kwh=0,
            battery_energy_after_kwh=50
        ))
        
    with pytest.raises(ScheduleValidationError, match="Energy balance failed"):
        validate_schedule(hours, battery, [], plan)
