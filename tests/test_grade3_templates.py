"""Tests for Grade 3 question templates."""
import pytest
from curriculum.templates.grade3 import GRADE3_TEMPLATES


REQUIRED_KEYS = {'skill_id', 'question', 'correct_answer', 'options', 'explanation', 'template_id', 'difficulty'}


class TestAllGrade3Templates:
    def test_all_skills_have_templates(self):
        expected = {'g3_mult_facts', 'g3_div_facts', 'g3_multi_digit_mult',
                    'g3_area_perimeter', 'g3_fraction_compare', 'g3_fraction_add_sub',
                    'g3_rounding', 'g3_mult_div_word', 'g3_elapsed_time', 'g3_data'}
        assert set(GRADE3_TEMPLATES.keys()) == expected

    def test_each_template_returns_valid_dict(self):
        for skill_id, templates in GRADE3_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                missing = REQUIRED_KEYS - set(result.keys())
                assert not missing, f'{skill_id}: missing keys {missing}'

    def test_correct_answer_in_options(self):
        for skill_id, templates in GRADE3_TEMPLATES.items():
            for fn in templates:
                for _ in range(5):
                    result = fn(800)
                    assert result['correct_answer'] in result['options'], \
                        f'{skill_id}: {result["correct_answer"]} not in {result["options"]}'

    def test_four_unique_options(self):
        for skill_id, templates in GRADE3_TEMPLATES.items():
            for fn in templates:
                for _ in range(5):
                    result = fn(800)
                    opts = result['options']
                    assert len(opts) == 4, f'{skill_id}: {len(opts)} options'
                    assert len(set(opts)) == 4, f'{skill_id}: duplicates in {opts}'

    def test_skill_id_matches(self):
        for skill_id, templates in GRADE3_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                assert result['skill_id'] == skill_id


class TestMultFacts:
    def test_product_is_correct(self):
        for _ in range(20):
            result = GRADE3_TEMPLATES['g3_mult_facts'][0](800)
            q = result['question']
            # Extract a × b from "What is a × b?"
            parts = q.replace('What is ', '').replace('?', '').split(' × ')
            a, b = int(parts[0]), int(parts[1])
            assert int(result['correct_answer']) == a * b


class TestDivFacts:
    def test_division_is_exact(self):
        for _ in range(20):
            result = GRADE3_TEMPLATES['g3_div_facts'][0](800)
            q = result['question']
            parts = q.replace('What is ', '').replace('?', '').split(' ÷ ')
            dividend, divisor = int(parts[0]), int(parts[1])
            assert dividend % divisor == 0
            assert int(result['correct_answer']) == dividend // divisor


class TestAreaPerimeter:
    def test_answer_is_positive(self):
        for _ in range(10):
            result = GRADE3_TEMPLATES['g3_area_perimeter'][0](800)
            assert int(result['correct_answer']) > 0


class TestRounding:
    def test_low_difficulty_rounds_to_10(self):
        for _ in range(10):
            result = GRADE3_TEMPLATES['g3_rounding'][0](600)
            answer = int(result['correct_answer'])
            assert answer % 10 == 0


class TestDataInterpretation:
    def test_valid_response(self):
        for _ in range(10):
            result = GRADE3_TEMPLATES['g3_data'][0](800)
            assert 'survey' in result['question'].lower() or 'shows' in result['question'].lower()
