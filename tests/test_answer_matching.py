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


# --- MCQ text↔letter resolution via options ---

def test_mcq_text_answer_correct_is_letter():
    """Student clicks '6' (text), correct_answer='B', options=['4','6','8','10']."""
    opts = ['4', '6', '8', '10']
    assert check_answer("6", "B", 'mcq', options=opts) == (True, False)


def test_mcq_text_answer_wrong_vs_letter():
    """Student clicks '4' (text), correct_answer='B' (which is '6')."""
    opts = ['4', '6', '8', '10']
    assert check_answer("4", "B", 'mcq', options=opts) == (False, False)


def test_mcq_letter_answer_correct_is_text():
    """Student somehow submits 'B', correct_answer='6' (text)."""
    opts = ['4', '6', '8', '10']
    assert check_answer("B", "6", 'mcq', options=opts) == (True, False)


def test_mcq_both_text_same():
    """Both student and correct are option text (same)."""
    opts = ['Paris', 'London', 'Berlin', 'Rome']
    assert check_answer("Paris", "Paris", 'mcq', options=opts) == (True, False)


def test_mcq_text_with_letter_prefix_options():
    """Options have letter prefixes like 'A) 4'."""
    opts = ['A) 4', 'B) 6', 'C) 8', 'D) 10']
    assert check_answer("6", "B", 'mcq', options=opts) == (True, False)


def test_mcq_no_options_fallback():
    """Without options, text vs letter can't resolve."""
    assert check_answer("6", "B", 'mcq') == (False, False)
