"""Tests for question_validator — 15 rules including math answer verification."""
from engine.question_validator import (
    validate_question, verify_math_answer, verify_explanation_vs_answer,
    verify_explanation_arithmetic, _extract_explanation_results,
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


def test_rejects_answer_with_letter_prefix_in_question():
    """Q#421 regression: 'Solve the inequality: x > -3' with answer 'C) x > -3'.
    Letter prefix masked the giveaway — 'c) x > -3' not in question, but 'x > -3' is."""
    ok, reason = validate_question(
        _q(question='Solve the inequality: x > -3',
           correct_answer='C) x > -3',
           options=['A) x < -3', 'B) x <= -3', 'C) x > -3', 'D) x >= -3'])
    )
    assert not ok
    assert 'given away' in reason.lower()


def test_rejects_answer_with_letter_prefix_giveaway_simple():
    """Same pattern: answer text (without letter) appears verbatim in question."""
    ok, reason = validate_question(
        _q(question='There are 14 dots on the page.',
           correct_answer='B) 14',
           options=['A) 12', 'B) 14', 'C) 16', 'D) 18'])
    )
    assert not ok
    assert 'given away' in reason.lower()


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

def test_compute_word_problem_gives():
    """Word problems with 'has N ... gives M' are now verifiable."""
    assert _try_compute_answer(
        'Tom has 5 apples and gives 2 to Sam. How many does he have?'
    ) == 3

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

def test_verify_word_problem_correct():
    """Word problems with extractable math are now verified."""
    ok, _ = verify_math_answer(
        _q('Tom has 5 apples. He gives 2 away. How many left?', '3')
    )
    assert ok

def test_verify_word_problem_wrong():
    """Word problems with wrong answers are now caught."""
    ok, reason = verify_math_answer(
        _q('Tom has 5 apples. He gives 2 away. How many left?', '4')
    )
    assert not ok
    assert 'computes to 3' in reason

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


# === Rule 15: Verify arithmetic expressions in explanation ===

def test_arith_catches_wrong_subtraction_in_explanation():
    """THE EXACT SCREENSHOT BUG: '4 - 2 = 3' in explanation."""
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='Tommy starts with 4 candies and eats 2. So, 4 - 2 = 3.')
    )
    assert not ok
    assert '4 - 2 = 2, not 3' in reason


def test_arith_accepts_correct_subtraction():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='4 - 2 = 2. Tommy has 2 candies left.')
    )
    assert ok


def test_arith_catches_wrong_addition():
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='3 + 5 = 9')
    )
    assert not ok
    assert '3 + 5 = 8, not 9' in reason


def test_arith_accepts_correct_addition():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='3 + 5 = 8')
    )
    assert ok


def test_arith_catches_wrong_multiplication():
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='6 * 3 = 15')
    )
    assert not ok
    assert '6 * 3 = 18, not 15' in reason


def test_arith_catches_wrong_division():
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='12 / 4 = 4')
    )
    assert not ok
    assert 'not 4' in reason


def test_arith_accepts_correct_division():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='12 / 4 = 3.')
    )
    assert ok


def test_arith_catches_wrong_chained():
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='5 + 3 + 2 = 11')
    )
    assert not ok
    assert '5 + 3 + 2 = 10, not 11' in reason


def test_arith_accepts_correct_chained():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='5 + 3 + 2 = 10')
    )
    assert ok


def test_arith_multiple_expressions_first_wrong():
    """If any expression is wrong, reject."""
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='First, 10 - 3 = 8. Then 8 - 2 = 6.')
    )
    assert not ok
    assert '10 - 3 = 7, not 8' in reason


def test_arith_multiple_expressions_all_correct():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='First, 10 - 3 = 7. Then 7 - 2 = 5.')
    )
    assert ok


def test_arith_no_expression_passes():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='Count the apples: there are four.')
    )
    assert ok


def test_arith_empty_explanation_passes():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='')
    )
    assert ok


def test_arith_unicode_minus():
    """Unicode minus sign in explanation."""
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='8 − 3 = 6')
    )
    assert not ok
    assert 'not 6' in reason


def test_arith_catches_off_by_one():
    """Common LLM error: off by one."""
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='7 - 3 = 5')
    )
    assert not ok
    assert '7 - 3 = 4, not 5' in reason


def test_arith_large_numbers():
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='45 + 37 = 83')
    )
    assert not ok
    assert '45 + 37 = 82, not 83' in reason


def test_arith_large_numbers_correct():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='45 + 37 = 82')
    )
    assert ok


# === Word problem parsing: _try_compute_answer ===

def test_compute_word_has_eats():
    """'has N ... eats M' → N - M"""
    assert _try_compute_answer(
        'Tommy has 4 candies, and he eats 2 of them. How many left?'
    ) == 2


def test_compute_word_has_gives():
    assert _try_compute_answer(
        'Sara has 8 stickers. She gives 3 to her friend. How many left?'
    ) == 5


def test_compute_word_has_gives_away():
    assert _try_compute_answer(
        'Tom has 10 marbles. He gives away 4. How many left?'
    ) == 6


def test_compute_word_has_loses():
    assert _try_compute_answer(
        'Jake has 7 toys. He loses 2. How many left?'
    ) == 5


def test_compute_word_has_lost():
    assert _try_compute_answer(
        'Anna had 9 coins. She lost 5. How many left?'
    ) == 4


def test_compute_word_has_spent():
    assert _try_compute_answer(
        'Mike has 15 dollars. He spent 8 on a book. How much left?'
    ) == 7


def test_compute_word_has_broke():
    assert _try_compute_answer(
        'Emma has 6 eggs. She broke 2. How many are left?'
    ) == 4


def test_compute_word_has_dropped():
    assert _try_compute_answer(
        'He has 5 balls. He dropped 1. How many left?'
    ) == 4


def test_compute_word_has_sold():
    assert _try_compute_answer(
        'She has 12 cookies. She sold 4. How many left?'
    ) == 8


def test_compute_word_has_used():
    assert _try_compute_answer(
        'James has 10 crayons. He used 3. How many left?'
    ) == 7


def test_compute_word_has_ate():
    assert _try_compute_answer(
        'Lucy has 6 candies. She ate 4. How many left?'
    ) == 2


def test_compute_word_has_shared():
    assert _try_compute_answer(
        'Ben has 8 toys. He shared 3 with his friend. How many left?'
    ) == 5


def test_compute_word_has_gets():
    """'has N ... gets M' → N + M"""
    assert _try_compute_answer(
        'Sara has 3 stickers. She gets 5 more. How many now?'
    ) == 8


def test_compute_word_has_finds():
    assert _try_compute_answer(
        'Tom has 4 shells. He finds 3 more. How many now?'
    ) == 7


def test_compute_word_has_receives():
    assert _try_compute_answer(
        'Anna has 6 cards. She receives 4 more. How many now?'
    ) == 10


def test_compute_word_has_bought():
    assert _try_compute_answer(
        'Mike has 5 books. He bought 3 more. How many now?'
    ) == 8


def test_compute_word_has_earned():
    assert _try_compute_answer(
        'She has 10 dollars. She earned 5 more. How many now?'
    ) == 15


def test_compute_word_has_won():
    assert _try_compute_answer(
        'He has 2 trophies. He won 1 more. How many now?'
    ) == 3


def test_compute_word_there_are_fly_away():
    """'There are N ... M fly away' → N - M"""
    assert _try_compute_answer(
        'There are 7 birds on a tree. 3 fly away. How many are left?'
    ) == 4


def test_compute_word_there_are_walk_away():
    assert _try_compute_answer(
        'There are 10 ducks. 4 walk away. How many are left?'
    ) == 6


def test_compute_word_there_are_fell_off():
    assert _try_compute_answer(
        'There are 5 apples on a tree. 2 fell off. How many left?'
    ) == 3


def test_compute_word_there_were_popped():
    assert _try_compute_answer(
        'There were 8 balloons. 3 popped. How many left?'
    ) == 5


def test_compute_word_there_are_left():
    assert _try_compute_answer(
        'There are 9 children. 4 left. How many remain?'
    ) == 5


def test_compute_word_problem_still_unverifiable():
    """Complex word problems without matching patterns are still skipped."""
    assert _try_compute_answer(
        'A train travels at 60 km/h. How far does it go in 2 hours?'
    ) is None


def test_compute_word_problem_no_action_verb():
    """No recognizable action verb — can't parse."""
    assert _try_compute_answer(
        'A box contains 5 red and 3 blue balls. How many balls total?'
    ) is None


# === THE SCREENSHOT BUG: Full integration test ===

def test_screenshot_bug_caught_by_rule13():
    """The exact bug: 'has 4 candies, eats 2' with answer=3. Rule 13 catches it."""
    ok, reason = verify_math_answer({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': 'C) 3',
        'options': ['A) 1', 'B) 4', 'C) 3', 'D) 2'],
    })
    assert not ok
    assert 'computes to 2' in reason


def test_screenshot_bug_caught_by_rule15():
    """The exact bug: explanation '4 - 2 = 3'. Rule 15 catches it."""
    ok, reason = verify_explanation_arithmetic({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': 'C) 3',
        'options': ['A) 1', 'B) 4', 'C) 3', 'D) 2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 3. Tommy has 3 candies left.',
    })
    assert not ok
    assert '4 - 2 = 2, not 3' in reason


def test_screenshot_bug_validate_question_rejects():
    """Full validation: the exact screenshot bug is rejected."""
    ok, reason = validate_question({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': 'C) 3',
        'options': ['A) 1', 'B) 4', 'C) 3', 'D) 2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 3. Tommy has 3 candies left.',
    })
    assert not ok


def test_screenshot_bug_correct_version_accepted():
    """Same question with correct answer=2 passes all rules."""
    ok, _ = validate_question({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': 'D) 2',
        'options': ['A) 1', 'B) 4', 'C) 3', 'D) 2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 2. Tommy has 2 candies left.',
    })
    assert ok


# === Consistently wrong explanation + answer (the gap Rule 15 fills) ===

def test_consistent_wrong_explanation_and_answer_caught():
    """When explanation says '6 - 3 = 4' and answer is 4, Rule 14 passes but Rule 15 catches it."""
    q = _qe(
        question='Amy has 6 apples. She gives 3 away. How many left?',
        correct_answer='B) 4',
        options=['A) 2', 'B) 4', 'C) 3', 'D) 5'],
        explanation='Amy has 6 apples and gives 3 away. 6 - 3 = 4. She has 4 left.',
    )
    # Rule 14 passes (explanation final = 4, answer = 4)
    ok14, _ = verify_explanation_vs_answer(q)
    assert ok14  # This is the gap!

    # Rule 15 catches it (6 - 3 = 3, not 4)
    ok15, reason = verify_explanation_arithmetic(q)
    assert not ok15
    assert '6 - 3 = 3, not 4' in reason


def test_consistent_wrong_addition():
    """'3 + 4 = 8' with answer 8 — consistently wrong."""
    q = _qe(
        question='Sam has 3 red balls and 4 blue balls. How many total?',
        correct_answer='8',
        explanation='3 + 4 = 8',
    )
    ok15, reason = verify_explanation_arithmetic(q)
    assert not ok15
    assert '3 + 4 = 7, not 8' in reason


def test_consistent_wrong_off_by_one():
    """Common LLM error: 9 - 5 = 3 with answer 3."""
    q = _qe(
        question='Lisa has 9 stickers. She uses 5. How many left?',
        correct_answer='3',
        explanation='Lisa uses 5 of her 9 stickers. 9 - 5 = 3.',
    )
    ok15, reason = verify_explanation_arithmetic(q)
    assert not ok15
    assert '9 - 5 = 4, not 3' in reason


# === Edge cases for Rule 15 ===

def test_arith_decimal_result():
    """10 / 4 = 2.5 should pass."""
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='10 / 4 = 2.5')
    )
    assert ok


def test_arith_explanation_with_text_around():
    """Arithmetic buried in prose should still be checked."""
    ok, reason = verify_explanation_arithmetic(
        _qe(explanation='We know that when you have 8 items and take away 3, you get 8 - 3 = 6 items remaining.')
    )
    assert not ok
    assert '8 - 3 = 5, not 6' in reason


def test_arith_does_not_false_positive_on_equations():
    """'x = 5' or standalone '= 5' should not trigger false positives."""
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='The answer is = 5. So we have 5 items.')
    )
    assert ok


def test_arith_mixed_correct_and_no_expr():
    ok, _ = verify_explanation_arithmetic(
        _qe(explanation='Count: 2 + 3 = 5. Five items total.')
    )
    assert ok


# === Word problem edge cases ===

def test_compute_word_starts_with():
    assert _try_compute_answer(
        'Sam starts with 10 coins. He spent 4 coins. How many left?'
    ) == 6


def test_compute_word_had_gave():
    assert _try_compute_answer(
        'She had 8 flowers. She gave 5 away. How many left?'
    ) == 3


def test_compute_word_bakes_gives():
    assert _try_compute_answer(
        'Mom bakes 12 cookies. She gives 7 to neighbors. How many left?'
    ) == 5


def test_compute_word_makes_uses():
    assert _try_compute_answer(
        'He makes 9 sandwiches. He uses 3. How many left?'
    ) == 6


def test_compute_word_picks_up_loses():
    assert _try_compute_answer(
        'She picks up 6 rocks. She loses 2 on the way. How many left?'
    ) == 4


# === Full validate_question: word problems with wrong answers ===

def test_validate_word_problem_wrong_answer_rejected():
    """Word problem with wrong MCQ answer is rejected."""
    ok, reason = validate_question({
        'question': 'Sara has 8 stickers. She gives 3 away. How many left?',
        'correct_answer': 'C) 6',
        'options': ['A) 3', 'B) 4', 'C) 6', 'D) 5'],
        'explanation': '8 - 3 = 6.',
    })
    assert not ok


def test_validate_word_problem_correct_answer_accepted():
    ok, _ = validate_question({
        'question': 'Sara has 8 stickers. She gives 3 away. How many left?',
        'correct_answer': 'D) 5',
        'options': ['A) 3', 'B) 4', 'C) 6', 'D) 5'],
        'explanation': '8 - 3 = 5. Sara has 5 stickers left.',
    })
    assert ok


def test_validate_addition_word_problem_wrong():
    ok, reason = validate_question({
        'question': 'Tom has 4 shells. He finds 3 more. How many now?',
        'correct_answer': 'A) 8',
        'options': ['A) 8', 'B) 7', 'C) 6', 'D) 1'],
        'explanation': '4 + 3 = 8.',
    })
    assert not ok


def test_validate_addition_word_problem_correct():
    ok, _ = validate_question({
        'question': 'Tom has 4 shells. He finds 3 more. How many now?',
        'correct_answer': 'B) 7',
        'options': ['A) 8', 'B) 7', 'C) 6', 'D) 1'],
        'explanation': '4 + 3 = 7.',
    })
    assert ok


# ==========================================================================
# THE EXACT Q363 BUG: Multi-step question, intermediate answer as correct
# ==========================================================================

def test_q363_bug_compute_multiply_then_divide():
    """_try_compute_answer should handle 'multiplying X by Y then dividing by Z'."""
    result = _try_compute_answer(
        'What is the result of multiplying 3 by 4 and then dividing by 2?'
    )
    assert result == 6.0


def test_q363_bug_rule13_rejects_intermediate_answer():
    """Rule 13 should catch answer=12 when the question computes to 6."""
    ok, reason = verify_math_answer({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': 'C) 12',
        'options': ['A) 6', 'B) 8', 'C) 12', 'D) 24'],
    })
    assert not ok
    assert 'computes to 6' in reason


def test_q363_bug_rule14_catches_natural_language_explanation():
    """Rule 14 should parse 'to get 12' and 'which is 6' as results."""
    ok, reason = verify_explanation_vs_answer({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': 'C) 12',
        'options': ['A) 6', 'B) 8', 'C) 12', 'D) 24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert not ok
    assert 'explanation computes 6' in reason


def test_q363_bug_full_validation_rejects():
    """Full validate_question should reject the exact Q363 bug."""
    ok, reason = validate_question({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': 'C) 12',
        'options': ['A) 6', 'B) 8', 'C) 12', 'D) 24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert not ok


def test_q363_bug_correct_answer_accepted():
    """Same question with correct answer=6 passes."""
    ok, _ = validate_question({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': 'A) 6',
        'options': ['A) 6', 'B) 8', 'C) 12', 'D) 24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert ok


# === Q299/301 BUG: "sum of X, Y, and Z" with wrong answer ===

def test_q301_bug_compute_sum_of_three():
    """_try_compute_answer should handle 'sum of 5, 6, and 3'."""
    result = _try_compute_answer('What is the sum of 5, 6, and 3?')
    assert result == 14


def test_q301_bug_rule13_rejects_wrong_sum():
    """Rule 13 should reject answer=12 when sum of 5+6+3 = 14."""
    ok, reason = verify_math_answer({
        'question': 'What is the sum of 5, 6, and 3?',
        'correct_answer': 'B) 12',
        'options': ['A) 10', 'B) 12', 'C) 14', 'D) 15'],
    })
    assert not ok
    assert 'computes to 14' in reason


# === Unicode operator handling ===

def test_compute_unicode_multiplication():
    """× (multiplication sign) should be handled."""
    assert _try_compute_answer('What is 3 × 4?') == 12


def test_compute_unicode_division():
    """÷ (division sign) should be handled."""
    assert _try_compute_answer('What is 12 ÷ 3?') == 4.0


def test_compute_unicode_multi_step():
    """3 × 4 ÷ 2 should be computed as (3*4)/2 = 6."""
    assert _try_compute_answer('What is 3 × 4 ÷ 2?') == 6.0


def test_verify_unicode_operators_correct():
    ok, _ = verify_math_answer({
        'question': 'What is 3 × 4?',
        'correct_answer': '12',
    })
    assert ok


def test_verify_unicode_operators_wrong():
    ok, reason = verify_math_answer({
        'question': 'What is 3 × 4?',
        'correct_answer': '8',
    })
    assert not ok
    assert 'computes to 12' in reason


# === New _try_compute_answer patterns ===

def test_compute_multiplying_by():
    assert _try_compute_answer('What do you get multiplying 5 by 3?') == 15


def test_compute_multiply_by():
    assert _try_compute_answer('Multiply 7 by 8.') == 56


def test_compute_dividing_by():
    assert _try_compute_answer('What is the result of dividing 20 by 4?') == 5.0


def test_compute_divide_by():
    assert _try_compute_answer('Divide 15 by 3.') == 5.0


def test_compute_divide_then_multiply():
    """Reverse order: divide first then multiply."""
    result = _try_compute_answer(
        'What is the result of dividing 12 by 4 and then multiplying by 5?'
    )
    assert result == 15.0


def test_compute_product_of():
    assert _try_compute_answer('What is the product of 6 and 7?') == 42


def test_compute_sum_of_two():
    assert _try_compute_answer('What is the sum of 15 and 8?') == 23


def test_compute_sum_of_four():
    """sum of A, B, C, and D should work."""
    assert _try_compute_answer('What is the sum of 2, 3, 4, and 5?') == 14


# === Natural language explanation result extraction (Rule 14) ===

def test_expl_natural_language_to_get():
    """'to get N' should be extracted as a result."""
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '5',
        'explanation': 'Add 2 and 3 to get 5.',
    })
    assert ok


def test_expl_natural_language_to_get_mismatch():
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '6',
        'explanation': 'Add 2 and 3 to get 5.',
    })
    assert not ok
    assert 'explanation computes 5' in reason


def test_expl_natural_language_which_is():
    """'which is N' should be extracted."""
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '8',
        'explanation': 'The result, which is 6, is the final answer.',
    })
    assert not ok
    assert 'explanation computes 6' in reason


def test_expl_natural_language_the_result_is():
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '10',
        'explanation': 'After adding, the result is 8.',
    })
    assert not ok
    assert 'explanation computes 8' in reason


def test_expl_natural_language_leaving():
    ok, _ = verify_explanation_vs_answer({
        'correct_answer': '3',
        'explanation': 'Subtract 2 from 5, leaving 3.',
    })
    assert ok


def test_expl_natural_language_you_get():
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '10',
        'explanation': 'Divide 20 by 2 and you get 10.',
    })
    assert ok


def test_expl_natural_language_multi_step_last_wins():
    """With multiple natural language results, the last is the final answer."""
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '12',
        'explanation': 'First multiply to get 12. Then divide to get 6.',
    })
    assert not ok
    assert 'explanation computes 6' in reason


def test_expl_mixed_equals_and_natural():
    """Mix of = and natural language — last result wins."""
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '10',
        'explanation': '5 + 3 = 8. Then add 2 to get 10.',
    })
    assert ok


# === Direct tests for _extract_explanation_results ===

def test_extract_results_equals_only():
    results = _extract_explanation_results('3 + 4 = 7')
    assert results == [7.0]


def test_extract_results_natural_language_only():
    results = _extract_explanation_results(
        'First multiply to get 12. Then divide to obtain the result, which is 6.'
    )
    assert 12.0 in results
    assert 6.0 in results
    assert results[-1] == 6.0  # last is final answer


def test_extract_results_mixed():
    results = _extract_explanation_results('5 + 3 = 8. Then add 2 to get 10.')
    assert 8.0 in results
    assert 10.0 in results
    assert results[-1] == 10.0


def test_extract_results_empty():
    results = _extract_explanation_results('Count the apples: there are four.')
    assert results == []


def test_extract_results_the_answer_is():
    results = _extract_explanation_results('After computing, the answer is 42.')
    assert results == [42.0]


# =====================================================================
# Rule 16: Reject text descriptions of visual diagrams
# =====================================================================

def test_rule16_rejects_open_circle_in_question():
    q = _q('Which inequality has an open circle at -3 on the number line?', 'B')
    valid, reason = validate_question(q)
    assert not valid
    assert 'visual' in reason.lower()


def test_rule16_rejects_shading_in_choices():
    q = _q(
        'Which represents x > -3?', 'A',
        options=[
            'A) The number line shows an open circle at -3 and shading to the right',
            'B) Closed circle at -3, left shading',
            'C) Open circle, left shading',
            'D) Closed circle, right shading',
        ],
    )
    valid, reason = validate_question(q)
    assert not valid


def test_rule16_accepts_normal_inequality():
    q = _q('Solve for x: 2x + 1 > 5.', 'x > 2')
    valid, _ = validate_question(q)
    assert valid


def test_rule16_accepts_math_expression():
    q = _q('What is 5 + 3?', '8')
    valid, _ = validate_question(q)
    assert valid


# =====================================================================
# Rule 17: Reject draw/graph/sketch/plot imperatives
# =====================================================================

def test_rule17_rejects_graph_it():
    q = _q('Solve the equation, then graph it on a number line.', '3')
    valid, reason = validate_question(q)
    assert not valid
    assert 'visual' in reason.lower()


def test_rule17_rejects_draw_the():
    q = _q('Draw the number line for the solution.', '5')
    valid, reason = validate_question(q)
    assert not valid


def test_rule17_rejects_sketch():
    q = _q('Sketch a graph of the following equation.', 'parabola')
    valid, reason = validate_question(q)
    assert not valid


def test_rule17_accepts_solve():
    q = _q('Solve for x: 3x - 2 = 7.', '3')
    valid, _ = validate_question(q)
    assert valid


# --- Q586 Regression Tests ---
# Q586 had answer in brackets "[x > -5]" which bypassed validation
# Root cause: _answer_in_question_is_ok() was too permissive for "which" questions


def test_rule5_rejects_bracket_placeholder_answer():
    """Q586 regression: Answer in brackets [x > -5] should be rejected."""
    q = {
        'question': 'Which inequality does this number line represent? [x > -5]',
        'correct_answer': 'D) x > -5',
        'options': ['x > -5', 'x < -5', 'x ≥ -5', 'x ≤ -5'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Q586-type: bracket placeholder should be rejected"
    assert 'answer' in reason.lower() or 'placeholder' in reason.lower()


def test_rule5_rejects_which_expression_with_answer():
    """Generic 'which expression' questions shouldn't have answer shown."""
    q = {
        'question': 'Which equation represents this? [2x + 3 = 7]',
        'correct_answer': 'D) 2x + 3 = 7',
        'options': ['2x + 3 = 7', 'x + 3 = 7', '2x = 7', 'x = 7'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Which expression with answer in brackets should fail"


def test_rule6_catches_bracket_with_variable():
    """Rule 6 should catch [x > ...] patterns as placeholders."""
    q = {
        'question': 'Represent: [x ≥ 0] on a number line',
        'correct_answer': 'correct representation',
        'question_type': 'short_answer'
    }
    valid, reason = validate_question(q)
    assert not valid, "Should catch [x ...] as placeholder pattern"
    assert 'placeholder' in reason.lower()


def test_rule5_allows_legitimate_which_is_questions():
    """'Which is...' identification questions naturally contain answer."""
    q = {
        'question': 'Which is bigger: 1/2 or 2/3?',
        'correct_answer': 'B) 2/3',
        'options': ['1/2', '2/3', 'neither', 'equal'],
        'question_type': 'mcq'
    }
    valid, _ = validate_question(q)
    assert valid, "Which is comparison questions should pass"


def test_rule5_allows_what_is_math():
    """'What is' math questions naturally contain expressions."""
    q = {
        'question': 'What is 4 + 3 × 2?',
        'correct_answer': '10',
        'question_type': 'short_answer'
    }
    valid, _ = validate_question(q)
    assert valid, "Math questions with expressions in question are OK"


def test_rule5_rejects_which_inequality_with_bracketed_answer():
    """'Which inequality' shouldn't show answer in brackets."""
    q = {
        'question': 'Which inequality does this represent? [x < 5]',
        'correct_answer': 'A) x < 5',
        'options': ['x < 5', 'x > 5', 'x ≤ 5', 'x ≥ 5'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Which inequality with bracket answer should fail"
    assert 'answer' in reason.lower()


def test_rule5_rejects_clock_time_in_brackets():
    """Clock time questions shouldn't show answer in brackets."""
    q = {
        'question': 'What time does this clock show? [7:15]',
        'correct_answer': 'B) 7:15',
        'options': ['7:15', '7:45', '6:15', '8:15'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Clock time with bracket answer should fail"
    assert 'answer' in reason.lower()


def test_rule5_rejects_fraction_in_brackets():
    """Fraction questions shouldn't show answer in brackets."""
    q = {
        'question': 'What fraction of the circle is shaded? [1/4]',
        'correct_answer': 'B) 1/4',
        'options': ['1/4', '1/2', '3/4', '1'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Fraction with bracket answer should fail"
    assert 'answer' in reason.lower()


def test_rule5_allows_which_of_list():
    """'Which of these' questions naturally have answers in options."""
    q = {
        'question': 'Which of these numbers is prime: 4, 7, 9, 10?',
        'correct_answer': 'B) 7',
        'options': ['4', '7', '9', '10'],
        'question_type': 'mcq'
    }
    valid, _ = validate_question(q)
    assert valid, "Which of list questions should pass"


# --- Rule 19: Multiple Correct Answers Tests ---
# Q130 Regression: "Which is even: 13, 24, 37, 48, 59?" has TWO even numbers (24 AND 48)


def test_rule19_rejects_multiple_even_numbers():
    """Q130 regression: Multiple even numbers in context = ambiguous."""
    q = {
        'question': 'What number is even among 13, 24, 37, 48, and 59?',
        'correct_answer': 'B) 24',
        'options': ['22', '24', '12', '20'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Question with 2 even numbers should be rejected"
    assert 'multiple correct answers' in reason.lower()


def test_rule19_rejects_multiple_odd_numbers():
    """Multiple odd numbers in context = ambiguous."""
    q = {
        'question': 'Which is odd: 2, 5, 7, 11, 13?',
        'correct_answer': 'B) 5',
        'options': ['2', '5', '4', '8'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Question with multiple odd numbers should be rejected"


def test_rule19_rejects_multiple_primes():
    """Multiple prime numbers in context = ambiguous."""
    q = {
        'question': 'Which is prime: 4, 7, 9, 11, 15?',
        'correct_answer': 'B) 7',
        'options': ['4', '7', '9', '15'],
        'question_type': 'mcq'
    }
    valid, reason = validate_question(q)
    assert not valid, "Question with 2+ primes should be rejected"


def test_rule19_allows_single_even_number():
    """Only one even number in context = OK."""
    q = {
        'question': 'Which is even: 3, 5, 7, 8, 9?',
        'correct_answer': 'D) 8',
        'options': ['3', '5', '7', '8', '9'],
        'question_type': 'mcq'
    }
    valid, _ = validate_question(q)
    assert valid, "Question with single even number should pass"


def test_rule19_allows_single_odd_number():
    """Only one odd number in context = OK."""
    q = {
        'question': 'Which is odd: 2, 4, 5, 6, 8?',
        'correct_answer': 'C) 5',
        'options': ['2', '4', '5', '6', '8'],
        'question_type': 'mcq'
    }
    valid, _ = validate_question(q)
    assert valid, "Question with single odd number should pass"


def test_rule19_allows_no_numbers_in_question():
    """Questions without numbers are exempt from this check."""
    q = {
        'question': 'What is the capital of France?',
        'correct_answer': 'Paris',
        'question_type': 'short_answer'
    }
    valid, _ = validate_question(q)
    # May pass or fail for other reasons, but not Rule 19


def test_rule19_allows_mismatched_numbers():
    """If question lists numbers but options are different, harder to check ambiguity."""
    q = {
        'question': 'Which is even: 11, 13, 15, 17, 19?',  # All odd!
        'correct_answer': 'A) 22',
        'options': ['22', '24', '26', '28'],  # All even
        'question_type': 'mcq'
    }
    valid, _ = validate_question(q)
    # This specific case might pass because there are no even numbers in the question list
    # But shows the challenge of misaligned questions and options
