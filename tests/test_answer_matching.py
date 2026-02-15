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


# --- Article-A regression (Q#1077 bug) ---

def test_mcq_article_a_not_treated_as_letter():
    """Options starting with article 'A' must not all match each other.

    Bug: _extract_letter('a rock') returned 'A', so 'A rock' vs 'A caterpillar'
    both extracted to letter 'A' and were graded as equal.
    """
    opts = ['A leaf', 'A rock', 'A caterpillar', 'A bicycle']
    # Wrong answer must be wrong
    assert check_answer("A rock", "A caterpillar", 'mcq', options=opts) == (False, False)
    # Correct answer must be correct
    assert check_answer("A caterpillar", "A caterpillar", 'mcq', options=opts) == (True, False)


def test_mcq_article_b_not_treated_as_letter():
    """Option starting with 'B' as part of a name must not extract as letter B."""
    opts = ['Abraham Lincoln', 'Benjamin Franklin', 'Calvin Coolidge', 'Dwight Eisenhower']
    assert check_answer("Benjamin Franklin", "Abraham Lincoln", 'mcq', options=opts) == (False, False)
    assert check_answer("Abraham Lincoln", "Abraham Lincoln", 'mcq', options=opts) == (True, False)
