"""Tests for computed distractors module."""
import pytest
from ai.distractors import (
    compute_distractors, insert_distractors, _parse_number,
    _numeric_distractors, _format_number
)


class TestParseNumber:
    def test_parse_integer(self):
        assert _parse_number('42') == 42

    def test_parse_float(self):
        assert _parse_number('3.14') == 3.14

    def test_parse_fraction(self):
        assert _parse_number('1/2') == 0.5

    def test_parse_latex_fraction(self):
        assert _parse_number(r'\frac{1}{2}') == 0.5

    def test_parse_negative(self):
        assert _parse_number('-5') == -5

    def test_parse_invalid(self):
        assert _parse_number('hello') is None


class TestNumericDistractors:
    def test_generates_enough_distractors(self):
        distractors = _numeric_distractors(10)
        assert len(distractors) >= 3

    def test_distractors_not_equal_to_correct(self):
        distractors = _numeric_distractors(10)
        assert '10' not in distractors

    def test_includes_off_by_one(self):
        distractors = _numeric_distractors(10)
        # Should have 9 and/or 11
        assert any(d in distractors for d in ['9', '11', '8', '12'])


class TestComputeDistractors:
    def test_returns_list(self):
        result = compute_distractors('12')
        assert isinstance(result, list)

    def test_correct_length(self):
        result = compute_distractors('12', num_options=4)
        assert len(result) == 3

    def test_numeric_answer(self):
        result = compute_distractors('42')
        assert len(result) >= 1

    def test_fraction_answer(self):
        result = compute_distractors('1/2')
        assert len(result) >= 1

    def test_text_fallback(self):
        result = compute_distractors('True')
        assert len(result) >= 1


class TestInsertDistractors:
    def test_adds_options_to_mcq(self):
        q = {'question': 'What is 7 + 5?', 'correct_answer': '12', 'question_type': 'mcq'}
        result = insert_distractors(q)
        assert result['options'] is not None
        assert len(result['options']) == 4
        # Correct answer should be in options
        assert any('12' in opt for opt in result['options'])

    def test_adds_letter_prefix(self):
        q = {'question': 'What is 7 + 5?', 'correct_answer': '12', 'question_type': 'mcq'}
        result = insert_distractors(q)
        # correct_answer should now have letter prefix
        assert ')' in result['correct_answer']

    def test_skips_non_mcq(self):
        q = {'question': 'What is 7 + 5?', 'correct_answer': '12', 'question_type': 'short_answer'}
        result = insert_distractors(q)
        # Options should remain None for non-MCQ
        assert result.get('options') is None
