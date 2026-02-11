"""Tests for engine/answer_matching.py."""
from engine.answer_matching import check_answer


def test_exact_match():
    assert check_answer("42", "42") == (True, False)


def test_case_insensitive():
    assert check_answer("Photosynthesis", "photosynthesis") == (True, False)


def test_numeric_equivalence():
    assert check_answer("3.0", "3")[0] is True


def test_mcq_letter():
    assert check_answer("B", "B", 'mcq') == (True, False)


def test_mcq_case_insensitive():
    assert check_answer("b", "B", 'mcq') == (True, False)


def test_mcq_wrong():
    assert check_answer("A", "C", 'mcq') == (False, False)


def test_wrong_answer():
    correct, close = check_answer("Jupiter", "Mars")
    assert correct is False


def test_empty_answer():
    assert check_answer("", "42") == (False, False)


def test_none_answer():
    assert check_answer(None, "42") == (False, False)


def test_whitespace():
    assert check_answer("  42  ", "42") == (True, False)
