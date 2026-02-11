"""Tests for question_validator — 14 rules including math answer verification."""
from engine.question_validator import (
    validate_question, verify_math_answer, verify_explanation_vs_answer,
    _try_compute_answer, _resolve_answer_text, _parse_numeric, _safe_eval_expr,
)


def _q(question='What is 2 + 2?', correct_answer='4', options=None):
    """Helper to build a question dict."""
    d = {'question': question, 'correct_answer': correct_answer}
    if options is not None:
        d['options'] = options
    return d


# --- Rule 1: Question minimum length ---

def test_rejects_empty_question():
    ok, reason = validate_question(_q(question=''))
    assert not ok
    assert 'too short' in reason.lower()


def test_rejects_short_question():
    ok, reason = validate_question(_q(question='Hi?'))
    assert not ok


def test_accepts_question_at_min_length():
    ok, _ = validate_question(_q(question='What is 2?'))
    assert ok


# --- Rule 2: Answer not empty or placeholder ---

def test_rejects_empty_answer():
    ok, reason = validate_question(_q(correct_answer=''))
    assert not ok
    assert 'placeholder' in reason.lower() or 'empty' in reason.lower()


def test_rejects_placeholder_answer_question_mark():
    ok, _ = validate_question(_q(correct_answer='?'))
    assert not ok


def test_rejects_placeholder_answer_na():
    ok, _ = validate_question(_q(correct_answer='N/A'))
    assert not ok


def test_rejects_placeholder_answer_none():
    ok, _ = validate_question(_q(correct_answer='none'))
    assert not ok


def test_rejects_placeholder_answer_ellipsis():
    ok, _ = validate_question(_q(correct_answer='...'))
    assert not ok


# --- Rule 3: Unique choices ---

def test_rejects_duplicate_choices():
    ok, reason = validate_question(
        _q(options=['A) Paris', 'B) Paris', 'C) London', 'D) Berlin'],
           correct_answer='A) Paris')
    )
    assert not ok
    assert 'duplicate' in reason.lower()


def test_rejects_whitespace_padded_duplicates():
    ok, _ = validate_question(
        _q(options=['Paris', ' Paris ', 'London', 'Berlin'],
           correct_answer='Paris')
    )
    assert not ok


# --- Rule 4: Correct answer in choices ---

def test_rejects_answer_not_in_choices():
    ok, reason = validate_question(
        _q(correct_answer='Tokyo',
           options=['A) Paris', 'B) London', 'C) Berlin', 'D) Rome'])
    )
    assert not ok
    assert 'not found in choices' in reason.lower()


def test_accepts_answer_in_choices():
    ok, _ = validate_question(
        _q(correct_answer='A) Paris',
           options=['A) Paris', 'B) London', 'C) Berlin', 'D) Rome'])
    )
    assert ok


def test_accepts_answer_by_letter():
    ok, _ = validate_question(
        _q(correct_answer='A',
           options=['A) Paris', 'B) London', 'C) Berlin', 'D) Rome'])
    )
    assert ok


# --- Rule 5: Answer not given away in question ---

def test_rejects_answer_giveaway():
    ok, reason = validate_question(
        _q(question='There are 14 dots on the page.',
           correct_answer='14')
    )
    assert not ok
    assert 'given away' in reason.lower()


def test_allows_answer_in_math_expression():
    ok, _ = validate_question(
        _q(question='What is 86 - 43?', correct_answer='43')
    )
    assert ok


def test_allows_answer_in_comparison():
    ok, _ = validate_question(
        _q(question='Which is bigger: 2/5 or 4/5?', correct_answer='4/5')
    )
    assert ok


def test_allows_answer_in_what_question():
    ok, _ = validate_question(
        _q(question='What is the capital of France?', correct_answer='France')
    )
    assert ok


def test_single_char_answer_skips_giveaway_check():
    ok, _ = validate_question(
        _q(question='The number 5 is odd. True or false?', correct_answer='5')
    )
    # Single char answers are allowed because they appear incidentally
    assert ok


# --- Rule 6: No placeholder text ---

def test_rejects_placeholder_text():
    ok, reason = validate_question(
        _q(question='[shows 5 apples] How many apples?')
    )
    assert not ok
    assert 'placeholder' in reason.lower()


def test_rejects_image_placeholder():
    ok, _ = validate_question(
        _q(question='[image of a cat] What animal is this?')
    )
    assert not ok


# --- Rule 7: Answer max length ---

def test_rejects_long_answer():
    ok, reason = validate_question(
        _q(correct_answer='x' * 201)
    )
    assert not ok
    assert 'too long' in reason.lower()


def test_accepts_answer_at_200_chars():
    ok, _ = validate_question(
        _q(correct_answer='x' * 200)
    )
    assert ok


# --- Rule 8: No HTML/markdown ---

def test_rejects_html_in_question():
    ok, reason = validate_question(
        _q(question='What is <b>bold</b> text?')
    )
    assert not ok
    assert 'html' in reason.lower() or 'markdown' in reason.lower()


def test_rejects_markdown_code_in_question():
    ok, _ = validate_question(
        _q(question='What does ```print()``` do?')
    )
    assert not ok


def test_rejects_html_in_answer():
    ok, _ = validate_question(
        _q(correct_answer='<b>bold</b>')
    )
    assert not ok


# --- Rule 9: Minimum 3 choices ---

def test_rejects_two_choices():
    ok, reason = validate_question(
        _q(options=['Yes', 'No'], correct_answer='Yes')
    )
    assert not ok
    assert 'too few' in reason.lower()


def test_accepts_three_choices():
    ok, _ = validate_question(
        _q(options=['A) Red', 'B) Blue', 'C) Green'], correct_answer='A) Red')
    )
    assert ok


# --- Rule 10: Answer length bias ---

def test_rejects_answer_much_longer_than_distractors():
    ok, reason = validate_question(
        _q(correct_answer='A very long and detailed answer that gives it away',
           options=[
               'A very long and detailed answer that gives it away',
               'No', 'Yes', 'Maybe',
           ])
    )
    assert not ok
    assert 'length bias' in reason.lower()


def test_accepts_similar_length_choices():
    ok, _ = validate_question(
        _q(correct_answer='The mitochondria',
           options=['The mitochondria', 'The nucleus', 'The ribosome', 'The membrane'])
    )
    assert ok


# --- Rule 11: No "all/none of the above" ---

def test_rejects_all_of_the_above():
    ok, reason = validate_question(
        _q(options=['A) Red', 'B) Blue', 'C) Green', 'D) All of the above'],
           correct_answer='D) All of the above')
    )
    assert not ok
    assert 'banned' in reason.lower()


def test_rejects_none_of_the_above():
    ok, reason = validate_question(
        _q(options=['A) Red', 'B) Blue', 'C) Green', 'D) None of the above'],
           correct_answer='A) Red')
    )
    assert not ok
    assert 'banned' in reason.lower()


def test_rejects_none_of_these():
    ok, _ = validate_question(
        _q(options=['A) Red', 'B) Blue', 'C) Green', 'D) None of these'],
           correct_answer='A) Red')
    )
    assert not ok


# --- Rule 12: Question must have punctuation ---

def test_rejects_question_without_punctuation():
    ok, reason = validate_question(
        _q(question='Tell me about photosynthesis')
    )
    assert not ok
    assert 'punctuation' in reason.lower() or 'imperative' in reason.lower()


def test_accepts_question_with_question_mark():
    ok, _ = validate_question(
        _q(question='What is photosynthesis?')
    )
    assert ok


def test_accepts_question_with_colon():
    ok, _ = validate_question(
        _q(question='Complete the following: 2 + 2 =')
    )
    # Has a colon
    assert ok


def test_accepts_question_with_imperative():
    ok, _ = validate_question(
        _q(question='Calculate the sum of 5 and 3', correct_answer='8')
    )
    assert ok


def test_accepts_question_with_solve():
    ok, _ = validate_question(
        _q(question='Solve for x in 2x = 10')
    )
    # "Solve" is an imperative verb, and there's a period-like structure
    assert ok


# --- Combined: valid question passes all rules ---

def test_accepts_valid_mcq():
    ok, _ = validate_question(
        _q(question='What is the capital of France?',
           correct_answer='A) Paris',
           options=['A) Paris', 'B) London', 'C) Berlin', 'D) Rome'])
    )
    assert ok


def test_accepts_valid_short_answer():
    ok, _ = validate_question(
        _q(question='What is 7 * 8?',
           correct_answer='56')
    )
    assert ok


def test_none_choices_accepted():
    ok, _ = validate_question(
        _q(question='What is 2 + 2?', correct_answer='4')
    )
    assert ok


def test_empty_choices_list_accepted():
    ok, _ = validate_question(
        _q(question='What is 2 + 2?', correct_answer='4', options=[])
    )
    assert ok


# === Rule 13: Mathematical answer verification ===

# --- _safe_eval_expr ---

def test_safe_eval_simple_addition():
    assert _safe_eval_expr('5 + 3') == 8

def test_safe_eval_subtraction():
    assert _safe_eval_expr('15 - 7') == 8

def test_safe_eval_multiplication():
    assert _safe_eval_expr('6 * 4') == 24

def test_safe_eval_division():
    assert _safe_eval_expr('12 / 4') == 3.0

def test_safe_eval_chained():
    assert _safe_eval_expr('5 + 3 + 2') == 10

def test_safe_eval_division_by_zero():
    assert _safe_eval_expr('5 / 0') is None

def test_safe_eval_rejects_function_calls():
    assert _safe_eval_expr('__import__("os")') is None

def test_safe_eval_rejects_letters():
    assert _safe_eval_expr('x + 1') is None

def test_safe_eval_empty():
    assert _safe_eval_expr('') is None


# --- _parse_numeric ---

def test_parse_numeric_integer():
    assert _parse_numeric('42') == 42.0

def test_parse_numeric_float():
    assert _parse_numeric('3.14') == 3.14

def test_parse_numeric_fraction():
    assert abs(_parse_numeric('1/2') - 0.5) < 0.001

def test_parse_numeric_word():
    assert _parse_numeric('hello') is None

def test_parse_numeric_empty():
    assert _parse_numeric('') is None


# --- _resolve_answer_text ---

def test_resolve_letter_prefix():
    assert _resolve_answer_text('D) 9', []) == '9'

def test_resolve_letter_to_option():
    opts = ['A) 7', 'B) 6', 'C) 8', 'D) 9']
    assert _resolve_answer_text('D', opts) == '9'

def test_resolve_plain_number():
    assert _resolve_answer_text('42', []) == '42'

def test_resolve_letter_b_to_option():
    opts = ['A) 10', 'B) 15', 'C) 20', 'D) 25']
    assert _resolve_answer_text('B', opts) == '15'


# --- _try_compute_answer ---

def test_compute_addition():
    assert _try_compute_answer('What is 5 + 3?') == 8

def test_compute_subtraction():
    assert _try_compute_answer('What is 15 - 7?') == 8

def test_compute_multiplication():
    assert _try_compute_answer('What is 6 * 4?') == 24

def test_compute_three_addends():
    assert _try_compute_answer('What is 5 + 3 + 2?') == 10

def test_compute_word_plus():
    assert _try_compute_answer('What is 5 plus 3?') == 8

def test_compute_word_minus():
    assert _try_compute_answer('What is 15 minus 7?') == 8

def test_compute_word_times():
    assert _try_compute_answer('What is 3 times 4?') == 12

def test_compute_word_divided_by():
    assert _try_compute_answer('What is 12 divided by 3?') == 4.0

def test_compute_word_three_addends():
    assert _try_compute_answer('What is 2 plus 3 plus 4?') == 9

def test_compute_more_than():
    assert _try_compute_answer('What is 7 more than 15?') == 22

def test_compute_less_than():
    assert _try_compute_answer('What number is 7 less than 15?') == 8

def test_compute_subtract_from():
    assert _try_compute_answer('Subtract 3 from 10.') == 7

def test_compute_sum_of():
    assert _try_compute_answer('What is the sum of 6 and 8?') == 14

def test_compute_add_and():
    assert _try_compute_answer('Add 5 and 9.') == 14

def test_compute_difference_between():
    assert _try_compute_answer('What is the difference between 15 and 7?') == 8

def test_compute_zero_plus_zero():
    assert _try_compute_answer('What is 0 plus 0?') == 0

def test_compute_missing_number_left_add():
    assert _try_compute_answer('__ + 5 = 12') == 7

def test_compute_missing_number_right_add():
    assert _try_compute_answer('8 + __ = 15') == 7

def test_compute_missing_number_left_sub():
    assert _try_compute_answer('__ - 3 = 5') == 8

def test_compute_missing_number_right_sub():
    assert _try_compute_answer('10 - __ = 4') == 6

def test_compute_missing_number_question_mark():
    assert _try_compute_answer('? + 5 = 12') == 7

def test_compute_equation_form():
    assert _try_compute_answer('8 + 9 = ?') == 17

def test_compute_unicode_minus():
    assert _try_compute_answer('What is 15 − 7?') == 8

def test_compute_endash_minus():
    assert _try_compute_answer('What is 15 – 7?') == 8

def test_compute_word_problem_unverifiable():
    """Word problems without clear math expressions can't be verified."""
    assert _try_compute_answer(
        'Tom has 5 apples and gives 2 to Sam. How many does he have?'
    ) is None

def test_compute_comparison_unverifiable():
    """Comparison questions can't be numerically verified."""
    assert _try_compute_answer('Which is greater, 15 or 9?') is None

def test_compute_10_more_than():
    assert _try_compute_answer('What is 10 more than 45?') == 55

def test_compute_10_less_than():
    assert _try_compute_answer('What is 10 less than 50?') == 40


# --- verify_math_answer (full integration) ---

def test_verify_correct_addition():
    ok, _ = verify_math_answer(_q('What is 5 + 3?', '8'))
    assert ok

def test_verify_wrong_addition():
    ok, reason = verify_math_answer(_q('What is 5 + 3?', '9'))
    assert not ok
    assert 'computes to 8' in reason

def test_verify_correct_subtraction():
    ok, _ = verify_math_answer(_q('What is 15 - 7?', '8'))
    assert ok

def test_verify_wrong_subtraction():
    """This is the exact bug from the screenshot: 15 - 7 = 9 (should be 8)."""
    ok, reason = verify_math_answer(_q('What is 15 - 7?', '9'))
    assert not ok
    assert 'computes to 8' in reason

def test_verify_wrong_less_than():
    """The screenshot bug: 'What number is 7 less than 15?' answer D) 9."""
    ok, reason = verify_math_answer(
        _q('What number is 7 less than 15?', 'D',
           options=['A) 7', 'B) 6', 'C) 8', 'D) 9'])
    )
    assert not ok
    assert 'computes to 8' in reason

def test_verify_correct_less_than():
    ok, _ = verify_math_answer(
        _q('What number is 7 less than 15?', 'C',
           options=['A) 7', 'B) 6', 'C) 8', 'D) 9'])
    )
    assert ok

def test_verify_mcq_letter_correct():
    ok, _ = verify_math_answer(
        _q('What is 5 + 3?', 'C',
           options=['A) 6', 'B) 7', 'C) 8', 'D) 9'])
    )
    assert ok

def test_verify_mcq_letter_wrong():
    ok, reason = verify_math_answer(
        _q('What is 5 + 3?', 'D',
           options=['A) 6', 'B) 7', 'C) 8', 'D) 9'])
    )
    assert not ok

def test_verify_non_numeric_answer_skipped():
    """Non-numeric answers can't be verified — benefit of the doubt."""
    ok, _ = verify_math_answer(
        _q('Which shape has 4 sides?', 'square')
    )
    assert ok

def test_verify_unparseable_question_skipped():
    """Questions without extractable math — benefit of the doubt."""
    ok, _ = verify_math_answer(
        _q('Tom has 5 apples. He gives 2 away. How many left?', '3')
    )
    assert ok

def test_verify_missing_number_correct():
    ok, _ = verify_math_answer(_q('__ + 5 = 12', '7'))
    assert ok

def test_verify_missing_number_wrong():
    ok, reason = verify_math_answer(_q('__ + 5 = 12', '8'))
    assert not ok

def test_verify_three_addends_correct():
    ok, _ = verify_math_answer(_q('What is 5 + 3 + 2?', '10'))
    assert ok

def test_verify_three_addends_wrong():
    ok, reason = verify_math_answer(_q('What is 5 + 3 + 2?', '11'))
    assert not ok


# --- Full validate_question with math check ---

def test_validate_rejects_wrong_math():
    """validate_question should reject questions with wrong answers."""
    ok, reason = validate_question(
        _q('What is 15 - 7?', '9')
    )
    assert not ok
    assert 'math verification' in reason.lower()

def test_validate_accepts_correct_math():
    ok, _ = validate_question(
        _q('What is 15 - 7?', '8')
    )
    assert ok

def test_validate_rejects_wrong_mcq_math():
    ok, reason = validate_question(
        _q('What is 5 + 3?', 'D) 9',
           options=['A) 6', 'B) 7', 'C) 8', 'D) 9'])
    )
    assert not ok
    assert 'math verification' in reason.lower()


# === Rule 14: Explanation vs answer cross-check ===

def _qe(question='What is 2 + 2?', correct_answer='4', explanation='', options=None):
    """Helper to build question dict with explanation."""
    d = {'question': question, 'correct_answer': correct_answer, 'explanation': explanation}
    if options is not None:
        d['options'] = options
    return d


def test_expl_catches_screenshot_bug():
    """The exact bug from the screenshot: answer says 3 but explanation computes 4."""
    ok, reason = verify_explanation_vs_answer(
        _qe(
            question='Tommy has 5 apples. He gets some more and now has 9. How many did he get?',
            correct_answer='A',
            options=['A) 3', 'B) 4', 'C) 5', 'D) 6'],
            explanation='So, 9 - 5 = 4 apples. Therefore, Tommy got 4 apples.',
        )
    )
    assert not ok
    assert 'explanation computes 4' in reason


def test_expl_correct_match():
    ok, _ = verify_explanation_vs_answer(
        _qe(
            correct_answer='B',
            options=['A) 3', 'B) 4', 'C) 5', 'D) 6'],
            explanation='9 - 5 = 4. Tommy got 4 apples.',
        )
    )
    assert ok


def test_expl_no_explanation_passes():
    ok, _ = verify_explanation_vs_answer(
        _qe(correct_answer='5', explanation='')
    )
    assert ok


def test_expl_non_numeric_answer_passes():
    ok, _ = verify_explanation_vs_answer(
        _qe(correct_answer='square', explanation='A square has 4 = 4 sides.')
    )
    assert ok


def test_expl_no_equals_in_explanation_passes():
    ok, _ = verify_explanation_vs_answer(
        _qe(correct_answer='4', explanation='Count the apples: four.')
    )
    assert ok


def test_expl_multiple_equals_uses_last():
    """When explanation has multiple =, the last one is the final answer."""
    ok, reason = verify_explanation_vs_answer(
        _qe(
            correct_answer='5',
            explanation='First, 10 - 3 = 7. Then 7 - 2 = 5.',
        )
    )
    assert ok


def test_expl_multiple_equals_mismatch():
    ok, reason = verify_explanation_vs_answer(
        _qe(
            correct_answer='7',
            explanation='First, 10 - 3 = 7. Then 7 - 2 = 5.',
        )
    )
    assert not ok
    assert 'explanation computes 5' in reason


def test_expl_mcq_letter_resolved():
    """MCQ letter answers should be resolved before comparison."""
    ok, reason = verify_explanation_vs_answer(
        _qe(
            correct_answer='C',
            options=['A) 10', 'B) 12', 'C) 15', 'D) 8'],
            explanation='5 + 7 = 12. The answer is 12.',
        )
    )
    assert not ok
    assert 'explanation computes 12' in reason


def test_validate_full_catches_explanation_mismatch():
    """validate_question should reject when explanation contradicts answer."""
    ok, reason = validate_question(
        _qe(
            question='Tommy has 5 apples and gets more. Now he has 9. How many did he get?',
            correct_answer='A',
            options=['A) 3', 'B) 4', 'C) 5', 'D) 6'],
            explanation='9 - 5 = 4.',
        )
    )
    assert not ok
    assert 'explanation contradicts' in reason.lower()
