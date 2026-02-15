"""Tests for question_validator — 5 structural rules + math verification."""
from engine.question_validator import (
    validate_question, verify_math_answer, verify_explanation_vs_answer,
    verify_explanation_arithmetic, _extract_explanation_results,
    _try_compute_answer, _parse_numeric, _safe_eval_expr,
)


def _q(question='What is 2 + 2?', correct_answer='4', options=None):
    """Helper to build a question dict."""
    d = {'question': question, 'correct_answer': correct_answer}
    if options is not None:
        d['options'] = options
    return d


def _qe(question='What is 2 + 2?', correct_answer='4', explanation='', options=None):
    """Helper to build question dict with explanation."""
    d = {'question': question, 'correct_answer': correct_answer, 'explanation': explanation}
    if options is not None:
        d['options'] = options
    return d


# === Rule 1: Question minimum length ===

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


# === Rule 2: Answer not empty or placeholder ===

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


# === Rule 3: MCQ options validation ===

def test_rejects_duplicate_choices():
    ok, reason = validate_question(
        _q(options=['Paris', 'Paris', 'London', 'Berlin'],
           correct_answer='Paris')
    )
    assert not ok
    assert 'duplicate' in reason.lower()


def test_rejects_whitespace_padded_duplicates():
    ok, _ = validate_question(
        _q(options=['Paris', ' Paris ', 'London', 'Berlin'],
           correct_answer='Paris')
    )
    assert not ok


def test_rejects_answer_not_in_choices():
    ok, reason = validate_question(
        _q(correct_answer='Tokyo',
           options=['Paris', 'London', 'Berlin', 'Rome'])
    )
    assert not ok
    assert 'not found in choices' in reason.lower()


def test_accepts_answer_in_choices():
    ok, _ = validate_question(
        _q(correct_answer='Paris',
           options=['Paris', 'London', 'Berlin', 'Rome'])
    )
    assert ok


def test_rejects_two_choices():
    ok, reason = validate_question(
        _q(options=['Yes', 'No'], correct_answer='Yes')
    )
    assert not ok
    assert 'too few' in reason.lower()


def test_accepts_three_choices():
    ok, _ = validate_question(
        _q(options=['Red', 'Blue', 'Green'], correct_answer='Red')
    )
    assert ok


# === Banned choices ===

def test_rejects_all_of_the_above():
    ok, reason = validate_question(
        _q(options=['Red', 'Blue', 'Green', 'All of the above'],
           correct_answer='All of the above')
    )
    assert not ok
    assert 'banned' in reason.lower()


def test_rejects_none_of_the_above():
    ok, reason = validate_question(
        _q(options=['Red', 'Blue', 'Green', 'None of the above'],
           correct_answer='Red')
    )
    assert not ok
    assert 'banned' in reason.lower()


def test_rejects_none_of_these():
    ok, _ = validate_question(
        _q(options=['Red', 'Blue', 'Green', 'None of these'],
           correct_answer='Red')
    )
    assert not ok


# === Rule 4: No HTML/markdown ===

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


# === Rule 5: No visual references ===

def test_rejects_visual_shows_placeholder():
    ok, reason = validate_question(
        _q(question='[shows 5 apples] How many apples?')
    )
    assert not ok
    assert 'visual' in reason.lower()


def test_rejects_image_placeholder():
    ok, _ = validate_question(
        _q(question='[image of a cat] What animal is this?')
    )
    assert not ok


def test_rejects_graph_it():
    ok, reason = validate_question(
        _q(question='Solve the equation, then graph it on a number line.', correct_answer='3')
    )
    assert not ok
    assert 'visual' in reason.lower()


def test_rejects_draw_the():
    ok, _ = validate_question(
        _q(question='Draw the number line for the solution.', correct_answer='5')
    )
    assert not ok


def test_rejects_sketch():
    ok, _ = validate_question(
        _q(question='Sketch a graph of the following equation.', correct_answer='parabola')
    )
    assert not ok


def test_accepts_solve_no_visual():
    ok, _ = validate_question(
        _q(question='Solve for x: 3x - 2 = 7.', correct_answer='3')
    )
    assert ok


# === Answer max length ===

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


# === Combined: valid question passes all rules ===

def test_accepts_valid_mcq():
    ok, _ = validate_question(
        _q(question='What is the capital of France?',
           correct_answer='Paris',
           options=['Paris', 'London', 'Berlin', 'Rome'])
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


# ===================================================================
# _safe_eval_expr
# ===================================================================

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


# ===================================================================
# _parse_numeric
# ===================================================================

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


# ===================================================================
# _try_compute_answer — direct arithmetic + word patterns
# ===================================================================

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

def test_compute_zero_plus_zero():
    assert _try_compute_answer('What is 0 plus 0?') == 0

def test_compute_equation_form():
    assert _try_compute_answer('8 + 9 = ?') == 17

def test_compute_unicode_minus():
    assert _try_compute_answer('What is 15 \u2212 7?') == 8

def test_compute_endash_minus():
    assert _try_compute_answer('What is 15 \u2013 7?') == 8

def test_compute_comparison_unverifiable():
    """Comparison questions can't be numerically verified."""
    assert _try_compute_answer('Which is greater, 15 or 9?') is None

def test_compute_non_math_unverifiable():
    """Non-math questions return None."""
    assert _try_compute_answer(
        'A train travels at 60 km/h. How far does it go in 2 hours?'
    ) is None


# ===================================================================
# verify_math_answer
# ===================================================================

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

def test_verify_non_numeric_answer_skipped():
    """Non-numeric answers can't be verified -- benefit of the doubt."""
    ok, _ = verify_math_answer(
        _q('Which shape has 4 sides?', 'square')
    )
    assert ok

def test_verify_three_addends_correct():
    ok, _ = verify_math_answer(_q('What is 5 + 3 + 2?', '10'))
    assert ok

def test_verify_three_addends_wrong():
    ok, reason = verify_math_answer(_q('What is 5 + 3 + 2?', '11'))
    assert not ok


# === Full validate_question with math check ===

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
        _q('What is 5 + 3?', '9',
           options=['6', '7', '8', '9'])
    )
    assert not ok
    assert 'math verification' in reason.lower()


# ===================================================================
# verify_explanation_vs_answer (Rule 14)
# ===================================================================

def test_expl_catches_screenshot_bug():
    """The exact bug: answer says 3 but explanation computes 4."""
    ok, reason = verify_explanation_vs_answer(
        _qe(
            question='Tommy has 5 apples. He gets some more and now has 9. How many did he get?',
            correct_answer='3',
            options=['3', '4', '5', '6'],
            explanation='So, 9 - 5 = 4 apples. Therefore, Tommy got 4 apples.',
        )
    )
    assert not ok
    assert 'explanation computes 4' in reason


def test_expl_correct_match():
    ok, _ = verify_explanation_vs_answer(
        _qe(
            correct_answer='4',
            options=['3', '4', '5', '6'],
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


def test_expl_mcq_answer_vs_explanation():
    """MCQ numeric answers should be compared against explanation."""
    ok, reason = verify_explanation_vs_answer(
        _qe(
            correct_answer='15',
            options=['10', '12', '15', '8'],
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
            correct_answer='3',
            options=['3', '4', '5', '6'],
            explanation='9 - 5 = 4.',
        )
    )
    assert not ok
    assert 'explanation contradicts' in reason.lower()


# ===================================================================
# verify_explanation_arithmetic (Rule 15)
# ===================================================================

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
        _qe(explanation='8 \u2212 3 = 6')
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


# ===================================================================
# _extract_explanation_results
# ===================================================================

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


# ===================================================================
# Natural language explanation extraction
# ===================================================================

def test_expl_natural_language_to_get():
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
    """Mix of = and natural language -- last result wins."""
    ok, reason = verify_explanation_vs_answer({
        'correct_answer': '10',
        'explanation': '5 + 3 = 8. Then add 2 to get 10.',
    })
    assert ok


# ===================================================================
# Screenshot bug: full integration tests
# ===================================================================

def test_screenshot_bug_caught_by_rule15():
    """The exact bug: explanation '4 - 2 = 3'. Rule 15 catches it."""
    ok, reason = verify_explanation_arithmetic({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': '3',
        'options': ['1', '4', '3', '2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 3. Tommy has 3 candies left.',
    })
    assert not ok
    assert '4 - 2 = 2, not 3' in reason


def test_screenshot_bug_validate_question_rejects():
    """Full validation: the exact screenshot bug is rejected."""
    ok, reason = validate_question({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': '3',
        'options': ['1', '4', '3', '2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 3. Tommy has 3 candies left.',
    })
    assert not ok


def test_screenshot_bug_correct_version_accepted():
    """Same question with correct answer=2 passes all rules."""
    ok, _ = validate_question({
        'question': 'Tommy has 4 candies, and he eats 2 of them. How many candies does Tommy have left?',
        'correct_answer': '2',
        'options': ['1', '4', '3', '2'],
        'explanation': 'Tommy starts with 4 candies and eats 2. So, 4 - 2 = 2. Tommy has 2 candies left.',
    })
    assert ok


# ===================================================================
# Consistently wrong explanation + answer
# ===================================================================

def test_consistent_wrong_explanation_and_answer_caught():
    """When explanation says '6 - 3 = 4' and answer is 4, Rule 14 passes but Rule 15 catches it."""
    q = _qe(
        question='Amy has 6 apples. She gives 3 away. How many left?',
        correct_answer='4',
        options=['2', '4', '3', '5'],
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
    """'3 + 4 = 8' with answer 8 -- consistently wrong."""
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


# ===================================================================
# Unicode operators
# ===================================================================

def test_compute_unicode_multiplication():
    assert _try_compute_answer('What is 3 \u00d7 4?') == 12

def test_compute_unicode_division():
    assert _try_compute_answer('What is 12 \u00f7 3?') == 4.0

def test_compute_unicode_multi_step():
    assert _try_compute_answer('What is 3 \u00d7 4 \u00f7 2?') == 6.0

def test_verify_unicode_operators_correct():
    ok, _ = verify_math_answer({
        'question': 'What is 3 \u00d7 4?',
        'correct_answer': '12',
    })
    assert ok

def test_verify_unicode_operators_wrong():
    ok, reason = verify_math_answer({
        'question': 'What is 3 \u00d7 4?',
        'correct_answer': '8',
    })
    assert not ok
    assert 'computes to 12' in reason


# ===================================================================
# Q363 bug: multi-step explanation with natural language
# ===================================================================

def test_q363_bug_rule14_catches_natural_language_explanation():
    """Rule 14 should parse 'to get 12' and 'which is 6' as results."""
    ok, reason = verify_explanation_vs_answer({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': '12',
        'options': ['6', '8', '12', '24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert not ok
    assert 'explanation computes 6' in reason


def test_q363_bug_full_validation_rejects():
    """Full validate_question should reject the exact Q363 bug."""
    ok, reason = validate_question({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': '12',
        'options': ['6', '8', '12', '24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert not ok


def test_q363_bug_correct_answer_accepted():
    """Same question with correct answer=6 passes."""
    ok, _ = validate_question({
        'question': 'What is the result of multiplying 3 by 4 and then dividing by 2?',
        'correct_answer': '6',
        'options': ['6', '8', '12', '24'],
        'explanation': 'First, multiply 3 by 4 to get 12. Then divide 12 by 2 to obtain the result, which is 6.',
    })
    assert ok
