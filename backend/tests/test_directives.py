import pytest
from app.api.models import DirectiveInterpretation
from app.validation.directive_validator import validate_directives, DirectiveValidationError

def test_validate_directives_valid():
    notes = ["Note 1"]
    interp = [
        DirectiveInterpretation(
            note_index=0,
            applies=True,
            directive_type="solar_reduction",
            structured_adjustment={"hours": [13, 14], "factor": 0.2},
            explanation="test"
        )
    ]
    res = validate_directives(notes, interp, 100)
    assert len(res) == 1

def test_validate_directives_invalid_hours():
    notes = ["Note 1"]
    interp = [
        DirectiveInterpretation(
            note_index=0,
            applies=True,
            directive_type="solar_reduction",
            structured_adjustment={"hours": [14, 13], "factor": 0.2}, # Unsorted
            explanation="test"
        )
    ]
    with pytest.raises(DirectiveValidationError):
        validate_directives(notes, interp, 100)

def test_validate_directives_no_op_invalid():
    notes = ["Note 1"]
    interp = [
        DirectiveInterpretation(
            note_index=0,
            applies=True, # Should be False
            directive_type="no_op",
            structured_adjustment={"hours": [1]}, # Should be null
            explanation="test"
        )
    ]
    with pytest.raises(DirectiveValidationError):
        validate_directives(notes, interp, 100)
