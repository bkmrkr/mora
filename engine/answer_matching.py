"""Answer matching for MCQ and short-answer grading.

Returns (is_correct, is_close) tuples.
"""
import re


def check_answer(student_answer, correct_answer, question_type='short_answer'):
    """Check if student_answer matches correct_answer.

    Returns (is_correct: bool, is_close: bool).
    """
    if not student_answer or not correct_answer:
        return False, False

    student = _normalize(student_answer)
    correct = _normalize(correct_answer)

    if question_type == 'mcq':
        return _check_mcq(student, correct)

    # Short answer: try exact, then numeric, then fuzzy
    if student == correct:
        return True, False

    # Numeric equivalence
    s_num = _to_number(student)
    c_num = _to_number(correct)
    if s_num is not None and c_num is not None:
        if abs(s_num - c_num) < 1e-9:
            return True, False
        if c_num != 0 and abs(s_num - c_num) / abs(c_num) < 0.01:
            return False, True  # within 1%

    # Contained check
    if correct in student or student in correct:
        if len(student) > 0 and len(correct) > 0:
            ratio = min(len(student), len(correct)) / max(len(student), len(correct))
            if ratio > 0.8:
                return True, False

    return False, _is_close(student, correct)


def _check_mcq(student, correct):
    """MCQ: match on letter (A/B/C/D) or full text."""
    # Extract letter if present
    s_letter = _extract_letter(student)
    c_letter = _extract_letter(correct)
    if s_letter and c_letter:
        return s_letter == c_letter, False
    # Full text match
    return student == correct, False


def _normalize(text):
    """Lowercase, strip whitespace and punctuation."""
    text = str(text).strip().lower()
    text = re.sub(r'[^\w\s\d.-]', '', text)
    return text.strip()


def _to_number(text):
    """Try to parse text as a number."""
    text = text.replace(',', '').strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _extract_letter(text):
    """Extract a single letter answer (A-D)."""
    text = text.strip().upper()
    if len(text) == 1 and text in 'ABCD':
        return text
    match = re.match(r'^([A-D])[.)\s]', text.upper())
    if match:
        return match.group(1)
    return None


def _is_close(student, correct):
    """Simple closeness check using character overlap."""
    if not student or not correct:
        return False
    common = set(student) & set(correct)
    if len(correct) == 0:
        return False
    overlap = len(common) / len(set(correct))
    return overlap > 0.7
