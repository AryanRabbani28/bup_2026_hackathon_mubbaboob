import json
import asyncio
import google.generativeai as genai
from typing import List
from pydantic import TypeAdapter

from app.api.models import DirectiveInterpretation, OptimizeRequest
from app.config import settings
from app.validation.directive_validator import validate_directives, DirectiveValidationError

PROMPT_TEMPLATE = """You are an expert energy campus operator interpreter.
You are given a list of natural-language notes from campus operators for a 24-hour scenario.
Battery capacity is: {battery_capacity_kwh} kWh.

Your task is to convert each note into EXACTLY ONE supported directive type.
Do not invent rules, demand changes, or unsupported constraints.

Allowed directive types:
1. `solar_reduction`: Reduce usable solar during specific hours.
   structured_adjustment: {{"hours": [...], "factor": number}}
   - factor is the usable fraction remaining (e.g., 80% reduction means factor = 0.2; 25% of forecast means factor = 0.25; half of forecast means factor = 0.5).
2. `minimum_battery_reserve`: Battery energy must remain at or above a required level.
   structured_adjustment: {{"hours": [...], "minimum_energy_kwh": number}}
   - If stated as an absolute kWh (e.g., "90 kWh"), use that numeric value.
   - If stated as a percentage of battery capacity (e.g., "50% of the battery capacity"), calculate: minimum_energy_kwh = (percentage / 100.0) * {battery_capacity_kwh}.
3. `no_charge_window`: Battery charging is unavailable during specific hours.
   structured_adjustment: {{"hours": [...]}}
4. `no_discharge_window`: Battery discharging is unavailable during specific hours.
   structured_adjustment: {{"hours": [...]}}
5. `max_grid_window`: Grid import/intake may not exceed a stated amount during specific hours.
   structured_adjustment: {{"hours": [...], "max_grid_kwh": number}}
6. `no_op`: The note does not affect the current 24-hour energy schedule (e.g. sports deadlines, cafeteria menus, library book returns, club notices, room booking changes).
   applies: false
   structured_adjustment: null

Important rules:
- Time windows are whole hours, start-inclusive and end-exclusive.
  Examples:
  - "noon until 2 PM" or "12 PM to 2 PM" -> [12, 13]
  - "1 PM to 3 PM" -> [13, 14]
  - "2 AM until 5 AM" -> [2, 3, 4]
  - "6 PM until 9 PM" -> [18, 19, 20]
  - "6 PM until 10 PM" -> [18, 19, 20, 21]
  - "7 PM until 9 PM" -> [19, 20]
  - "7 PM until 10 PM" -> [19, 20, 21]
  - "10 AM until noon" -> [10, 11]
  - "11 AM until 1 PM" -> [11, 12]
  - "11 AM until 2 PM" -> [11, 12, 13]
  - "2 PM until 4 PM" -> [14, 15]
  - "5 PM until 7 PM" -> [17, 18]
- Hours must be unique integers between 0 and 23, sorted in strictly ascending order.
- For `no_op`: applies MUST be false, directive_type MUST be "no_op", and structured_adjustment MUST be null.
- For all other directives: applies MUST be true, and structured_adjustment MUST match the required shape.
- Return a JSON array containing EXACTLY ONE entry per input note, in exact note_index order: 0, 1, ... N-1.

Output JSON Format:
[
  {{
    "note_index": 0,
    "applies": true,
    "directive_type": "solar_reduction",
    "structured_adjustment": {{"hours": [12, 13], "factor": 0.25}},
    "explanation": "Short human-readable reason."
  }}
]

Input Notes:
{notes}
"""

async def call_gemini(prompt: str, model_name: str) -> str:
    genai.configure(api_key=settings.gemini_api_key, transport='rest')
    model = genai.GenerativeModel(model_name)
    response = await asyncio.to_thread(
        model.generate_content,
        prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.0
        ),
        request_options={"timeout": settings.gemini_timeout_seconds}
    )
    return response.text

async def interpret_operator_notes(request: OptimizeRequest) -> List[DirectiveInterpretation]:
    notes = "\n".join([f"{i}. {note}" for i, note in enumerate(request.operator_notes)])
    prompt = PROMPT_TEMPLATE.format(
        notes=notes, 
        battery_capacity_kwh=request.battery.capacity_kwh
    )
    
    adapter = TypeAdapter(List[DirectiveInterpretation])
    
    for attempt in range(settings.gemini_max_retries + 1):
        try:
            model_to_use = settings.gemini_model if attempt == 0 else settings.gemini_fallback_model
            raw_response = await call_gemini(prompt, model_to_use)
            
            # Pydantic validation
            interpretations = adapter.validate_json(raw_response)
            
            # Deterministic guardrails
            valid_interpretations = validate_directives(
                request.operator_notes, 
                interpretations, 
                request.battery.capacity_kwh
            )
            return valid_interpretations
        
        except (json.JSONDecodeError, ValueError, DirectiveValidationError) as e:
            if attempt < settings.gemini_max_retries:
                # Provide the error back to the model for repair
                prompt += f"\n\nYour previous output was invalid. Error: {str(e)}\nPlease fix it and output the valid JSON array."
                await asyncio.sleep(1)
            else:
                raise Exception(f"Failed to interpret notes after {settings.gemini_max_retries} retries: {str(e)}")
        except Exception as e:
            if attempt < settings.gemini_max_retries:
                if "ResourceExhausted" in str(e) or "429" in str(e):
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(1)
            else:
                raise Exception(f"Gemini API failure: {str(e)}")
    raise Exception(f"Failed to interpret notes after {settings.gemini_max_retries} retries.")
