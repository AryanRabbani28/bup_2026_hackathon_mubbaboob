from typing import List
from app.api.models import DirectiveInterpretation, OptimizeRequest

class DirectiveValidationError(Exception):
    pass

def validate_directives(
    operator_notes: List[str], 
    interpretations: List[DirectiveInterpretation],
    battery_capacity: float
) -> List[DirectiveInterpretation]:
    """
    Validates LLM output against deterministic guardrails.
    Returns the valid list or raises DirectiveValidationError.
    """
    if len(interpretations) != len(operator_notes):
        raise DirectiveValidationError(f"Expected {len(operator_notes)} interpretations, got {len(interpretations)}")

    # Check note mapping
    indices = [interp.note_index for interp in interpretations]
    if indices != list(range(len(operator_notes))):
        raise DirectiveValidationError(f"Interpretations must be in note_index order 0 to {len(operator_notes)-1}")

    for interp in interpretations:
        # Check applies semantics
        if interp.directive_type == "no_op":
            if interp.applies is not False:
                raise DirectiveValidationError(f"no_op must have applies=False. Note index: {interp.note_index}")
            if interp.structured_adjustment is not None:
                raise DirectiveValidationError(f"no_op must have null structured_adjustment. Note index: {interp.note_index}")
            continue

        if not interp.applies:
            raise DirectiveValidationError(f"Non-no_op directive {interp.directive_type} must have applies=True. Note index: {interp.note_index}")

        adj = interp.structured_adjustment
        if adj is None:
            raise DirectiveValidationError(f"Non-no_op directive {interp.directive_type} requires structured_adjustment. Note index: {interp.note_index}")

        # Check hours array
        if "hours" not in adj or not isinstance(adj["hours"], list):
            raise DirectiveValidationError(f"structured_adjustment must contain 'hours' list. Note index: {interp.note_index}")
        
        hours = adj["hours"]
        if not all(isinstance(h, int) and 0 <= h <= 23 for h in hours):
            raise DirectiveValidationError(f"hours must be integers from 0 to 23. Note index: {interp.note_index}")
        
        if sorted(list(set(hours))) != hours:
            raise DirectiveValidationError(f"hours must be unique and sorted ascending. Note index: {interp.note_index}")

        # Directive specific rules
        if interp.directive_type == "solar_reduction":
            if "factor" not in adj or not isinstance(adj["factor"], (int, float)):
                raise DirectiveValidationError(f"solar_reduction requires 'factor' number. Note index: {interp.note_index}")
            if not (0.0 <= adj["factor"] <= 1.0):
                raise DirectiveValidationError(f"solar_reduction factor must be between 0 and 1. Note index: {interp.note_index}")

        elif interp.directive_type == "minimum_battery_reserve":
            if "minimum_energy_kwh" not in adj or not isinstance(adj["minimum_energy_kwh"], (int, float)):
                raise DirectiveValidationError(f"minimum_battery_reserve requires 'minimum_energy_kwh' number. Note index: {interp.note_index}")
            if adj["minimum_energy_kwh"] < 0 or adj["minimum_energy_kwh"] > battery_capacity:
                raise DirectiveValidationError(f"minimum_energy_kwh must be >= 0 and <= capacity. Note index: {interp.note_index}")

        elif interp.directive_type == "max_grid_window":
            if "max_grid_kwh" not in adj or not isinstance(adj["max_grid_kwh"], (int, float)):
                raise DirectiveValidationError(f"max_grid_window requires 'max_grid_kwh' number. Note index: {interp.note_index}")
            if adj["max_grid_kwh"] < 0:
                raise DirectiveValidationError(f"max_grid_kwh must be non-negative. Note index: {interp.note_index}")
        
        elif interp.directive_type in ["no_charge_window", "no_discharge_window"]:
            pass # Only hours are required, already checked
        
    return interpretations
