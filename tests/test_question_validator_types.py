"""Tests for question_validator type safety — non-string values from LLM."""
from engine.question_validator import validate_question


def test_numeric_correct_answer_int():
    """LLM returns correct_answer as int — should not crash."""
    q = {'question': 'What is 5 + 3?', 'correct_answer': 8, 'explanation': '5 + 3 = 8'}
    is_valid, reason = validate_question(q)
    assert isinstance(is_valid, bool)


def test_numeric_correct_answer_float():
    """LLM returns correct_answer as float."""
    q = {'question': 'What is 1/2 as a decimal?', 'correct_answer': 0.5, 'explanation': '1/2 = 0.5'}
    is_valid, reason = validate_question(q)
    assert isinstance(is_valid, bool)


def test_options_as_string():
    """LLM returns options as a single string instead of list."""
    q = {
        'question': 'What is 2 + 2?',
        'correct_answer': '4',
        'options': 'A) 3, B) 4, C) 5, D) 6',
        'explanation': '2 + 2 = 4',
    }
    is_valid, reason = validate_question(q)
    # Should not crash — options coerced to empty list
    assert isinstance(is_valid, bool)


def test_none_values():
    """All None values — should return invalid, not crash."""
    q = {'question': None, 'correct_answer': None, 'options': None}
    is_valid, reason = validate_question(q)
    assert is_valid is False


def test_empty_dict():
    """Empty dict — should return invalid, not crash."""
    q = {}
    is_valid, reason = validate_question(q)
    assert is_valid is False
