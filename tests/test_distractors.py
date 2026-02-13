"""Tests for computed distractors module."""
import pytest
from ai.distractors import (
    compute_distractors, insert_distractors, _parse_number,
    _numeric_distractors, _format_number, _multi_value_distractors,
    _text_distractors
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
        result, success, reason = insert_distractors(q)
        assert success, reason
        assert result['options'] is not None
        assert len(result['options']) == 4
        # Correct answer should be in options
        assert any('12' in opt for opt in result['options'])

    def test_adds_letter_prefix(self):
        q = {'question': 'What is 7 + 5?', 'correct_answer': '12', 'question_type': 'mcq'}
        result, success, reason = insert_distractors(q)
        assert success, reason
        # correct_answer should now have letter prefix
        assert ')' in result['correct_answer']

    def test_skips_non_mcq(self):
        q = {'question': 'What is 7 + 5?', 'correct_answer': '12', 'question_type': 'short_answer'}
        result, success, reason = insert_distractors(q)
        # Options should remain None for non-MCQ
        assert result.get('options') is None


class TestMultiValueDistractors:
    """Test handling of multi-value answers like '2, 3' (for systems of equations, etc)."""

    def test_multi_value_distractors_basic(self):
        """Test generating distractors for '2, 3'."""
        distractors = _multi_value_distractors('2, 3')
        assert len(distractors) >= 2
        # Should not include the correct answer
        assert '2, 3' not in distractors

    def test_multi_value_distractors_not_duplicates(self):
        """Ensure generated distractors are not identical."""
        distractors = _multi_value_distractors('2, 3')
        assert len(distractors) == len(set(distractors)), \
            f"Distractors have duplicates: {distractors}"

    def test_multi_value_includes_off_by_one(self):
        """Off-by-one should be among the distractors."""
        distractors = _multi_value_distractors('2, 3')
        # Should have something like '3, 4' or '1, 2'
        assert any('3' in d or '1' in d for d in distractors)

    def test_compute_distractors_multi_value(self):
        """Test full compute_distractors for multi-value answer."""
        distractors = compute_distractors('2, 3', num_options=4)
        assert len(distractors) == 3
        assert '2, 3' not in distractors
        # All distractors should be unique
        assert len(distractors) == len(set(distractors)), \
            f"Computed distractors have duplicates: {distractors}"

    def test_insert_distractors_multi_value(self):
        """Test that multi-value answers get proper options without duplicates."""
        q = {
            'question': 'Solve x^2 - 5x + 6 = 0',
            'correct_answer': '2, 3',
            'question_type': 'mcq'
        }
        result, success, reason = insert_distractors(q)
        assert success, reason

        # Should have exactly 4 options
        assert len(result['options']) == 4
        # All options should be unique
        assert len(result['options']) == len(set(result['options'])), \
            f"Options have duplicates: {result['options']}"
        # Correct answer should be in options
        assert any('2, 3' in opt for opt in result['options'])
        # No option should be just '0' repeated
        zero_count = sum(1 for opt in result['options'] if opt == '0')
        assert zero_count <= 1, f"Too many '0' options: {result['options']}"

    def test_insert_distractors_no_all_zeros(self):
        """Regression test for Q491 bug: ensure not all options are '0'."""
        q = {
            'question': 'Solve x^2 - 5x + 6 = 0 by factoring.',
            'correct_answer': '2, 3',
            'question_type': 'mcq'
        }
        result, success, reason = insert_distractors(q)
        assert success, reason
        options = result['options']

        # Count how many options are just '0'
        zero_count = sum(1 for opt in options if opt == '0')

        # Should have at most 1 option with '0' (as one of the distractors)
        assert zero_count <= 1, \
            f"Too many '0' options (bug like Q491): {options}"

        # Better: verify all options are distinct
        assert len(set(options)) == len(options), \
            f"Duplicate options found: {options}"

    def test_text_distractors_multi_value(self):
        """Test _text_distractors directly for multi-value answers."""
        result = _text_distractors('2, 3')
        assert isinstance(result, list)
        assert len(result) > 0
        assert '2, 3' not in result
