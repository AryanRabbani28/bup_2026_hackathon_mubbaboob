import json
import asyncio
import google.generativeai as genai
from typing import List
from pydantic import TypeAdapter

from app.api.models import DirectiveInterpretation, OptimizeRequest
from app.config import settings
from app.validation.directive_validator import validate_directives, DirectiveValidationError

genai.configure(api_key=settings.gemini_api_key)

PROMPT_TEMPLATE = """
You are an expert energy campus operator interpreter.
You are given a list of natural-language notes from campus operators for a 24-hour scenario.
Your task is to convert each note into EXACTLY ONE supported directive type.
Do not invent rules, demand changes, or unsupported constraints.

Allowed directive types:
1. `solar_reduction`: Reduce usable solar. Requires structured_adjustment like {{"hours": [13, 14], "factor": 0.2}}. Factor is the usable fraction remaining (e.g., 80% drop means factor=0.2).
2. `minimum_battery_reserve`: Battery energy must remain at or above a reserve. Requires {{"hours": [18, 19], "minimum_energy_kwh": 120}}.
3. `no_charge_window`: Battery charging is unavailable. Requires {{"hours": [14, 15]}}.
4. `no_discharge_window`: Battery discharging is unavailable. Requires {{"hours": [17, 18]}}.
5. `max_grid_window`: Grid import limit. Requires {{"hours": [19, 20], "max_grid_kwh": 180}}.
6. `no_op`: Use when the note does not affect the current 24-hour energy schedule. Requires applies=false and structured_adjustment=null.

Important rules:
- Time windows are whole hours, start-inclusive and end-exclusive. E.g., "1 PM to 3 PM" means hours [13, 14].
- Hours must be unique, integers 0-23, sorted ascending.
- Non-`no_op` directives must have applies=true.
- Return exactly one entry per input note, in the exact same order (note_index 0, 1, 2...).

Input Notes:
{notes}
"""

async def call_gemini(prompt: str, model_name: str) -> str:
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
    prompt = PROMPT_TEMPLATE.format(notes=notes)
    
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
                # add short backoff if we want, but for now just retry immediately
                await asyncio.sleep(1)
            else:
                # Re-raise or handle as 500
                raise Exception(f"Failed to interpret notes after {settings.gemini_max_retries} retries: {str(e)}")
        except Exception as e:
            # For network errors, timeouts, etc.
            if attempt < settings.gemini_max_retries:
                await asyncio.sleep(1)
            else:
                raise Exception(f"Gemini API failure: {str(e)}")
