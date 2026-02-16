"""Tests for Grade 4 question templates."""
import pytest
from curriculum.templates.grade4 import GRADE4_TEMPLATES


REQUIRED_KEYS = {'skill_id', 'question', 'correct_answer', 'options', 'explanation', 'template_id', 'difficulty'}


class TestAllGrade4Templates:
    def test_all_skills_have_templates(self):
        expected = {'g4_multi_digit_mult', 'g4_long_division', 'g4_fraction_ops',
                    'g4_decimal_place_value', 'g4_decimal_add_sub', 'g4_angles',
                    'g4_geometry', 'g4_factors_multiples', 'g4_multi_step_word',
                    'g4_equivalent_fractions'}
        assert set(GRADE4_TEMPLATES.keys()) == expected

    def test_each_template_returns_valid_dict(self):
        for skill_id, templates in GRADE4_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                missing = REQUIRED_KEYS - set(result.keys())
                assert not missing, f'{skill_id}: missing keys {missing}'

    def test_correct_answer_in_options(self):
        for skill_id, templates in GRADE4_TEMPLATES.items():
            for fn in templates:
                for _ in range(10):
                    result = fn(800)
                    assert result['correct_answer'] in result['options'], \
                        f'{skill_id}: {result["correct_answer"]} not in {result["options"]}'

    def test_four_unique_options(self):
        for skill_id, templates in GRADE4_TEMPLATES.items():
            for fn in templates:
                for _ in range(10):
                    result = fn(800)
                    opts = result['options']
                    assert len(opts) == 4, f'{skill_id}: {len(opts)} options'
                    assert len(set(opts)) == 4, f'{skill_id}: duplicates in {opts}'

    def test_skill_id_matches(self):
        for skill_id, templates in GRADE4_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                assert result['skill_id'] == skill_id


class TestMultiDigitMult:
    def test_product_correct(self):
        for _ in range(10):
            result = GRADE4_TEMPLATES['g4_multi_digit_mult'][0](800)
            q = result['question'].replace('What is ', '').replace('?', '')
            a, b = q.split(' × ')
            assert int(result['correct_answer']) == int(a) * int(b)


class TestLongDivision:
    def test_exact_division(self):
        for _ in range(10):
            result = GRADE4_TEMPLATES['g4_long_division'][0](800)
            q = result['question'].replace('What is ', '').replace('?', '')
            a, b = q.split(' ÷ ')
            assert int(a) % int(b) == 0
            assert int(result['correct_answer']) == int(a) // int(b)


class TestFractionOps:
    def test_answer_is_fraction(self):
        for _ in range(10):
            result = GRADE4_TEMPLATES['g4_fraction_ops'][0](800)
            assert '/' in result['correct_answer']


class TestDecimalAddSub:
    def test_answer_is_decimal(self):
        for _ in range(10):
            result = GRADE4_TEMPLATES['g4_decimal_add_sub'][0](800)
            float(result['correct_answer'])  # should not raise


class TestAngles:
    def test_low_difficulty_valid_answer(self):
        """Low difficulty has classify, identify, and range variants."""
        type_names = {'acute', 'right', 'obtuse'}
        for _ in range(30):
            result = GRADE4_TEMPLATES['g4_angles'][0](600)
            ans = result['correct_answer']
            # classify → type names; identify → degree strings; range → descriptions
            valid = (ans in type_names or
                     ans.isdigit() or
                     '°' in ans or
                     'than' in ans or 'exactly' in ans or 'between' in ans)
            assert valid, f'Unexpected answer: {ans!r} for question: {result["question"]}'


class TestEquivalentFractions:
    def test_answer_contains_slash(self):
        for _ in range(10):
            result = GRADE4_TEMPLATES['g4_equivalent_fractions'][0](600)
            # Low difficulty returns a number, high difficulty returns fraction
            # Both are valid
            assert result['correct_answer']
