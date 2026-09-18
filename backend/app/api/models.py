from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator

class HourEntry(BaseModel):
    hour: int
    demand_kwh: float
    solar_kwh: float
    tariff_bdt_per_kwh: float

    @field_validator("hour", mode="before")
    @classmethod
    def validate_hour(cls, v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError("hour must be an integer, not boolean or float")
        if not (0 <= v <= 23):
            raise ValueError("hour must be between 0 and 23")
        return v

    @field_validator("demand_kwh", "solar_kwh", "tariff_bdt_per_kwh", mode="before")
    @classmethod
    def validate_non_negative_number(cls, v: Any) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("value must be a numeric type, not boolean")
        if v < 0:
            raise ValueError("value must be non-negative")
        return float(v)

class BatteryData(BaseModel):
    capacity_kwh: float
    initial_energy_kwh: float
    minimum_energy_kwh: float
    max_charge_kwh_per_hour: float
    max_discharge_kwh_per_hour: float

    @field_validator("capacity_kwh", mode="before")
    @classmethod
    def validate_capacity(cls, v: Any) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("capacity must be a numeric type, not boolean")
        if v <= 0:
            raise ValueError("capacity_kwh must be greater than 0")
        return float(v)

    @field_validator("initial_energy_kwh", "minimum_energy_kwh", "max_charge_kwh_per_hour", "max_discharge_kwh_per_hour", mode="before")
    @classmethod
    def validate_battery_numbers(cls, v: Any) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("value must be a numeric type, not boolean")
        if v < 0:
            raise ValueError("value must be non-negative")
        return float(v)

    @model_validator(mode="after")
    def validate_battery_invariants(self) -> "BatteryData":
        if self.initial_energy_kwh > self.capacity_kwh:
            raise ValueError("initial_energy_kwh cannot exceed capacity_kwh")
        if self.minimum_energy_kwh > self.capacity_kwh:
            raise ValueError("minimum_energy_kwh cannot exceed capacity_kwh")
        if self.initial_energy_kwh < self.minimum_energy_kwh:
            raise ValueError("initial_energy_kwh cannot be below minimum_energy_kwh")
        return self

class OptimizeRequest(BaseModel):
    scenario_id: str
    operator_notes: List[str] = Field(..., min_length=1, max_length=3)
    hours: List[HourEntry] = Field(..., min_length=24, max_length=24)
    battery: BatteryData

    @field_validator("scenario_id", mode="before")
    @classmethod
    def validate_scenario_id(cls, v: Any) -> str:
        if isinstance(v, bool) or not isinstance(v, str) or not v.strip():
            raise ValueError("scenario_id must be a non-empty string")
        return v

    @field_validator("operator_notes", mode="before")
    @classmethod
    def validate_operator_notes(cls, v: Any) -> List[str]:
        if not isinstance(v, list) or len(v) < 1 or len(v) > 3:
            raise ValueError("operator_notes must contain between 1 and 3 items")
        for idx, note in enumerate(v):
            if isinstance(note, bool) or not isinstance(note, str) or not note.strip():
                raise ValueError(f"operator_notes[{idx}] must be a non-empty string")
        return v

    @model_validator(mode="after")
    def validate_hours_sequence(self) -> "OptimizeRequest":
        hours_sequence = [h.hour for h in self.hours]
        if hours_sequence != list(range(24)):
            raise ValueError("hours must be 24 entries with hour sequentially ordered from 0 to 23")
        return self

class DirectiveInterpretation(BaseModel):
    note_index: int
    applies: bool
    directive_type: Literal[
        "solar_reduction",
        "minimum_battery_reserve",
        "no_charge_window",
        "no_discharge_window",
        "max_grid_window",
        "no_op"
    ]
    structured_adjustment: Optional[Dict[str, Any]] = None
    explanation: str

class HourlyPlanEntry(BaseModel):
    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: Literal["charge", "discharge", "idle"]
    battery_kwh: float
    battery_energy_after_kwh: float

class OptimizeResponse(BaseModel):
    scenario_id: str
    directive_interpretation: List[DirectiveInterpretation]
    hourly_plan: List[HourlyPlanEntry] = Field(..., min_length=24, max_length=24)
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str
