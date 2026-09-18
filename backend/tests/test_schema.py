import pytest
from pydantic import ValidationError
from app.api.models import OptimizeRequest, HourEntry, BatteryData, OptimizeResponse, DirectiveInterpretation, HourlyPlanEntry

def test_optimize_request_valid():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=5, tariff_bdt_per_kwh=7) for i in range(24)]
    battery = BatteryData(capacity_kwh=100, initial_energy_kwh=50, minimum_energy_kwh=10, max_charge_kwh_per_hour=20, max_discharge_kwh_per_hour=20)
    req = OptimizeRequest(scenario_id="1", operator_notes=["Note 1"], hours=hours, battery=battery)
    assert req.scenario_id == "1"

def test_optimize_request_invalid_hours_length():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=5, tariff_bdt_per_kwh=7) for i in range(23)] # only 23
    battery = BatteryData(capacity_kwh=100, initial_energy_kwh=50, minimum_energy_kwh=10, max_charge_kwh_per_hour=20, max_discharge_kwh_per_hour=20)
    with pytest.raises(ValidationError):
        OptimizeRequest(scenario_id="1", operator_notes=["Note 1"], hours=hours, battery=battery)

def test_optimize_request_invalid_notes_length():
    hours = [HourEntry(hour=i, demand_kwh=10, solar_kwh=5, tariff_bdt_per_kwh=7) for i in range(24)]
    battery = BatteryData(capacity_kwh=100, initial_energy_kwh=50, minimum_energy_kwh=10, max_charge_kwh_per_hour=20, max_discharge_kwh_per_hour=20)
    with pytest.raises(ValidationError):
        OptimizeRequest(scenario_id="1", operator_notes=[], hours=hours, battery=battery)
