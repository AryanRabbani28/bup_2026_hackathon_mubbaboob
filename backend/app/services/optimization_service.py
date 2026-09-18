import traceback
from app.api.models import OptimizeRequest, OptimizeResponse
from app.llm.interpreter import interpret_operator_notes
from app.optimization.optimizer import optimize_schedule
from app.validation.schedule_validator import validate_schedule

async def process_optimization_request(request: OptimizeRequest) -> OptimizeResponse:
    # 1. Interpret notes
    interpretations = await interpret_operator_notes(request)
    
    # 2. Optimize schedule
    plan, cost = optimize_schedule(request.hours, request.battery, interpretations)
    
    # 3. Independent validation
    # If the optimizer is buggy, this will raise an exception and fail safely
    total_grid, total_cost, peak_grid = validate_schedule(
        request.hours, request.battery, interpretations, plan
    )
    
    # 4. Generate plan summary (deterministic)
    active_types = [d.directive_type for d in interpretations if d.applies]
    if active_types:
        summary = f"Applied operator constraints ({', '.join(set(active_types))}). "
    else:
        summary = "No applicable operator constraints. "
    summary += "Used available solar, shifted battery energy across tariff periods, and restored battery to initial level."
    
    # 5. Return exact response
    return OptimizeResponse(
        scenario_id=request.scenario_id,
        directive_interpretation=interpretations,
        hourly_plan=plan,
        total_grid_kwh=total_grid,
        total_cost_bdt=total_cost,
        peak_grid_kwh=peak_grid,
        plan_summary=summary
    )
