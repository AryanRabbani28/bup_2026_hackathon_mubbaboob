from typing import List, Tuple
import numpy as np
from scipy.optimize import linprog
import math

from app.api.models import HourEntry, BatteryData, DirectiveInterpretation, HourlyPlanEntry

def optimize_schedule(
    hours: List[HourEntry],
    battery: BatteryData,
    directives: List[DirectiveInterpretation]
) -> Tuple[List[HourlyPlanEntry], float]:
    """
    Solves the 24-hour energy optimization problem using scipy.optimize.linprog.
    Returns (hourly_plan, optimized_total_cost).
    """
    N = 24
    if len(hours) != N:
        raise ValueError("hours must have exactly 24 entries")
    
    # Pre-calculate effective solar
    effective_solar = [h.solar_kwh for h in hours]
    for directive in directives:
        if directive.applies and directive.directive_type == "solar_reduction":
            adj = directive.structured_adjustment
            factor = adj["factor"]
            for hr in adj["hours"]:
                effective_solar[hr] *= factor
    
    # Directives that apply to bounds
    min_reserve = [battery.minimum_energy_kwh] * N
    max_grid = [float('inf')] * N
    
    no_charge = [False] * N
    no_discharge = [False] * N
    
    for directive in directives:
        if not directive.applies:
            continue
        adj = directive.structured_adjustment
        
        if directive.directive_type == "minimum_battery_reserve":
            for hr in adj["hours"]:
                min_reserve[hr] = max(min_reserve[hr], adj["minimum_energy_kwh"])
        elif directive.directive_type == "max_grid_window":
            for hr in adj["hours"]:
                max_grid[hr] = min(max_grid[hr], adj["max_grid_kwh"])
        elif directive.directive_type == "no_charge_window":
            for hr in adj["hours"]:
                no_charge[hr] = True
        elif directive.directive_type == "no_discharge_window":
            for hr in adj["hours"]:
                no_discharge[hr] = True

    # Variables for each hour h:
    # 0..23: grid[h]
    # 24..47: solar_used[h]
    # 48..71: battery_flow[h]  (positive = charge, negative = discharge)
    # 72..95: energy_after[h]
    num_vars = 4 * N
    
    c = np.zeros(num_vars)
    for i in range(N):
        c[i] = hours[i].tariff_bdt_per_kwh  # Objective is to minimize cost
    
    # Bounds
    bounds = []
    for i in range(N):
        # grid bounds
        bounds.append((0, max_grid[i]))
    for i in range(N):
        # solar bounds
        bounds.append((0, effective_solar[i]))
    for i in range(N):
        # battery_flow bounds
        lower = 0 if no_discharge[i] else -battery.max_discharge_kwh_per_hour
        upper = 0 if no_charge[i] else battery.max_charge_kwh_per_hour
        bounds.append((lower, upper))
    for i in range(N):
        # energy_after bounds
        bounds.append((min_reserve[i], battery.capacity_kwh))
        
    # Equality constraints (A_eq @ x = b_eq)
    A_eq = []
    b_eq = []
    
    # 1. Energy balance: grid[h] + solar_used[h] = demand[h] + battery_flow[h]
    # => grid[h] + solar_used[h] - battery_flow[h] = demand[h]
    for i in range(N):
        row = np.zeros(num_vars)
        row[i] = 1 # grid
        row[N + i] = 1 # solar
        row[2*N + i] = -1 # battery_flow
        A_eq.append(row)
        b_eq.append(hours[i].demand_kwh)
        
    # 2. Battery transition: energy_after[h] = energy_before[h] + battery_flow[h]
    # For h=0: energy_after[0] - battery_flow[0] = initial_energy
    # For h>0: energy_after[h] - energy_after[h-1] - battery_flow[h] = 0
    for i in range(N):
        row = np.zeros(num_vars)
        row[3*N + i] = 1 # energy_after[i]
        row[2*N + i] = -1 # battery_flow[i]
        if i == 0:
            A_eq.append(row)
            b_eq.append(battery.initial_energy_kwh)
        else:
            row[3*N + i - 1] = -1 # -energy_after[i-1]
            A_eq.append(row)
            b_eq.append(0)
            
    # 3. End-of-day neutrality: energy_after[23] = initial_energy
    row = np.zeros(num_vars)
    row[3*N + 23] = 1
    A_eq.append(row)
    b_eq.append(battery.initial_energy_kwh)
    
    # Solve
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    
    if not res.success:
        raise Exception(f"Optimization failed: {res.message}")
        
    x = res.x
    grid = x[0:N]
    solar_used = x[N:2*N]
    battery_flow = x[2*N:3*N]
    energy_after = x[3*N:4*N]
    
    plan = []
    tolerance = 1e-6
    for i in range(N):
        g = grid[i]
        s = solar_used[i]
        bf = battery_flow[i]
        ea = energy_after[i]
        
        # Clean up tolerances
        if abs(g) < tolerance: g = 0.0
        if abs(s) < tolerance: s = 0.0
        if abs(bf) < tolerance: bf = 0.0
        
        if bf > 0:
            action = "charge"
            bkwh = bf
        elif bf < 0:
            action = "discharge"
            bkwh = -bf
        else:
            action = "idle"
            bkwh = 0.0
            
        plan.append(HourlyPlanEntry(
            hour=i,
            grid_kwh=g,
            solar_used_kwh=s,
            battery_action=action,
            battery_kwh=bkwh,
            battery_energy_after_kwh=ea
        ))
        
    return plan, res.fun
