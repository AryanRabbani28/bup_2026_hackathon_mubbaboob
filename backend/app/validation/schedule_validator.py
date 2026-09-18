from typing import List, Tuple
from app.api.models import HourEntry, BatteryData, DirectiveInterpretation, HourlyPlanEntry

class ScheduleValidationError(Exception):
    pass

def validate_schedule(
    hours: List[HourEntry],
    battery: BatteryData,
    directives: List[DirectiveInterpretation],
    plan: List[HourlyPlanEntry]
) -> Tuple[float, float, float]:
    """
    Independently replays and validates the final schedule.
    Returns (total_grid_kwh, total_cost_bdt, peak_grid_kwh) if valid.
    Raises ScheduleValidationError if any rule is broken.
    """
    if len(plan) != 24:
        raise ScheduleValidationError(f"Expected 24 plan entries, got {len(plan)}")
    
    # Calculate effective constraints
    effective_solar = [h.solar_kwh for h in hours]
    min_reserve = [battery.minimum_energy_kwh] * 24
    max_grid = [float('inf')] * 24
    no_charge = [False] * 24
    no_discharge = [False] * 24

    for d in directives:
        if not d.applies:
            continue
        adj = d.structured_adjustment
        dtype = d.directive_type
        for hr in adj["hours"]:
            if dtype == "solar_reduction":
                effective_solar[hr] *= adj["factor"]
            elif dtype == "minimum_battery_reserve":
                min_reserve[hr] = max(min_reserve[hr], adj["minimum_energy_kwh"])
            elif dtype == "max_grid_window":
                max_grid[hr] = min(max_grid[hr], adj["max_grid_kwh"])
            elif dtype == "no_charge_window":
                no_charge[hr] = True
            elif dtype == "no_discharge_window":
                no_discharge[hr] = True

    tolerance = 0.01
    
    current_battery_energy = battery.initial_energy_kwh
    
    total_grid = 0.0
    total_cost = 0.0
    peak_grid = 0.0

    for h in range(24):
        entry = plan[h]
        if entry.hour != h:
            raise ScheduleValidationError(f"Hour mismatch at index {h}")
        
        # Grid checks
        if entry.grid_kwh < -tolerance:
            raise ScheduleValidationError(f"Negative grid energy at hour {h}")
        if entry.grid_kwh > max_grid[h] + tolerance:
            raise ScheduleValidationError(f"Grid cap exceeded at hour {h}")
        
        # Solar checks
        if entry.solar_used_kwh < -tolerance:
            raise ScheduleValidationError(f"Negative solar used at hour {h}")
        if entry.solar_used_kwh > effective_solar[h] + tolerance:
            raise ScheduleValidationError(f"Solar limit exceeded at hour {h}. Used: {entry.solar_used_kwh}, Available: {effective_solar[h]}")
        
        # Battery action
        if entry.battery_action == "idle":
            if abs(entry.battery_kwh) > tolerance:
                raise ScheduleValidationError(f"Idle action but battery_kwh > 0 at hour {h}")
            charge = 0.0
            discharge = 0.0
        elif entry.battery_action == "charge":
            if entry.battery_kwh < -tolerance:
                raise ScheduleValidationError(f"Negative battery_kwh at hour {h}")
            if no_charge[h] and entry.battery_kwh > tolerance:
                raise ScheduleValidationError(f"Charging during no_charge_window at hour {h}")
            if entry.battery_kwh > battery.max_charge_kwh_per_hour + tolerance:
                raise ScheduleValidationError(f"Max charge rate exceeded at hour {h}")
            charge = entry.battery_kwh
            discharge = 0.0
        elif entry.battery_action == "discharge":
            if entry.battery_kwh < -tolerance:
                raise ScheduleValidationError(f"Negative battery_kwh at hour {h}")
            if no_discharge[h] and entry.battery_kwh > tolerance:
                raise ScheduleValidationError(f"Discharging during no_discharge_window at hour {h}")
            if entry.battery_kwh > battery.max_discharge_kwh_per_hour + tolerance:
                raise ScheduleValidationError(f"Max discharge rate exceeded at hour {h}")
            charge = 0.0
            discharge = entry.battery_kwh
        else:
            raise ScheduleValidationError(f"Invalid battery action at hour {h}")
            
        # Energy balance
        lhs = entry.grid_kwh + entry.solar_used_kwh + discharge
        rhs = hours[h].demand_kwh + charge
        if abs(lhs - rhs) > tolerance:
            raise ScheduleValidationError(f"Energy balance failed at hour {h}. LHS: {lhs}, RHS: {rhs}")
            
        # Battery transition
        current_battery_energy = current_battery_energy + charge - discharge
        
        if abs(current_battery_energy - entry.battery_energy_after_kwh) > tolerance:
            raise ScheduleValidationError(f"Battery state transition mismatch at hour {h}")
            
        # Bounds
        if current_battery_energy < min_reserve[h] - tolerance:
            raise ScheduleValidationError(f"Battery below reserve at hour {h}. Has: {current_battery_energy}, Needs: {min_reserve[h]}")
        if current_battery_energy > battery.capacity_kwh + tolerance:
            raise ScheduleValidationError(f"Battery capacity exceeded at hour {h}")

        total_grid += entry.grid_kwh
        total_cost += entry.grid_kwh * hours[h].tariff_bdt_per_kwh
        if entry.grid_kwh > peak_grid:
            peak_grid = entry.grid_kwh
            
    # Final end of day
    if abs(current_battery_energy - battery.initial_energy_kwh) > tolerance:
        raise ScheduleValidationError("End-of-day battery neutrality failed")

    return total_grid, total_cost, peak_grid
