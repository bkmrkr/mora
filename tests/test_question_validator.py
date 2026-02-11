"""Tests for question_validator — ported from kidtutor's 11 applicable rules."""
from engine.question_validator import validate_question


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
        _q(question='Calculate the sum of 5 and 3')
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
