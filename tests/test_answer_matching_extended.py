"""Extended tests for engine/answer_matching.py — fractions, percentages, edge cases."""
from engine.answer_matching import check_answer, _normalize


# --- Normalization preserves critical characters ---

def test_normalize_preserves_slash():
    assert '/' in _normalize('3/4')


def test_normalize_preserves_percent():
    assert '%' in _normalize('50%')


def test_normalize_preserves_dollar():
    assert '$' in _normalize('$100')


# --- Fraction handling ---

def test_fraction_exact():
    assert check_answer('3/4', '3/4')[0] is True


def test_fraction_not_collapsed():
    """Without slash preservation, '3/4' would become '34'."""
    correct, _ = check_answer('3/4', '34')
    assert correct is False


# --- Percentage handling ---

def test_percent_exact():
    assert check_answer('50%', '50%')[0] is True


def test_percent_vs_decimal():
    """50% and 0.5 are different representations — not auto-matched."""
    correct, _ = check_answer('50%', '0.5')
    assert correct is False


# --- MCQ edge cases ---

def test_mcq_letter_with_period():
    """Student answers 'B.' instead of 'B'."""
    assert check_answer('B.', 'B', 'mcq') == (True, False)


def test_mcq_lowercase_answer():
    assert check_answer('c', 'C', 'mcq') == (True, False)


def test_mcq_text_both_no_options():
    """Both text answers that don't match — no resolution possible."""
    assert check_answer('Paris', 'London', 'mcq') == (False, False)


# --- Short answer edge cases ---

def test_contained_check_high_ratio():
    """'oxygen' contained in 'oxygens' with high ratio -> correct."""
    assert check_answer('oxygens', 'oxygen')[0] is True


def test_contained_check_low_ratio():
    """'cat' in 'concatenation' has low ratio -> not correct."""
    assert check_answer('concatenation', 'cat')[0] is False


def test_numeric_close():
    """Within 1% = close but not correct."""
    _, is_close = check_answer('101', '100')
    assert is_close is True


def test_numeric_far():
    """200 vs 100 = not close."""
    correct, is_close = check_answer('200', '100')
    assert correct is False
    assert is_close is False
