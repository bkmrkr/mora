"""Tests for Grade 2 question templates."""
import pytest
from curriculum.templates.grade2 import GRADE2_TEMPLATES


REQUIRED_KEYS = {'skill_id', 'question', 'correct_answer', 'options', 'explanation', 'template_id'}


class TestAllGrade2Templates:
    def test_all_skills_have_templates(self):
        expected = {'g2_add_sub_100', 'g2_add_sub_1000', 'g2_intro_multiply',
                    'g2_money', 'g2_time', 'g2_measurement', 'g2_fractions_intro',
                    'g2_comparing_3digit', 'g2_two_step', 'g2_odd_even'}
        assert set(GRADE2_TEMPLATES.keys()) == expected

    def test_each_template_returns_valid_dict(self):
        for skill_id, templates in GRADE2_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                missing = REQUIRED_KEYS - set(result.keys())
                assert not missing, f'{skill_id}: missing keys {missing}'

    def test_correct_answer_in_options(self):
        for skill_id, templates in GRADE2_TEMPLATES.items():
            for fn in templates:
                for _ in range(5):
                    result = fn(800)
                    assert result['correct_answer'] in result['options'], \
                        f'{skill_id}: {result["correct_answer"]} not in {result["options"]}'

    def test_four_unique_options(self):
        for skill_id, templates in GRADE2_TEMPLATES.items():
            for fn in templates:
                for _ in range(5):
                    result = fn(800)
                    opts = result['options']
                    assert len(opts) == 4, f'{skill_id}: {len(opts)} options'
                    assert len(set(opts)) == 4, f'{skill_id}: duplicates in {opts}'

    def test_skill_id_matches(self):
        for skill_id, templates in GRADE2_TEMPLATES.items():
            for fn in templates:
                result = fn(800)
                assert result['skill_id'] == skill_id


class TestAddSubWithin100:
    def test_answers_within_range(self):
        for _ in range(20):
            result = GRADE2_TEMPLATES['g2_add_sub_100'][0](800)
            answer = int(result['correct_answer'])
            assert 0 <= answer <= 99


class TestIntroMultiply:
    def test_answer_is_product(self):
        for _ in range(10):
            result = GRADE2_TEMPLATES['g2_intro_multiply'][0](800)
            assert 'bags' in result['question'] or 'group' in result['question'].lower()
            assert int(result['correct_answer']) > 0


class TestMoney:
    def test_answer_is_positive(self):
        for _ in range(10):
            result = GRADE2_TEMPLATES['g2_money'][0](800)
            assert int(result['correct_answer']) > 0
            assert 'cents' in result['question']


class TestFractionsIntro:
    def test_answer_is_integer(self):
        for _ in range(10):
            result = GRADE2_TEMPLATES['g2_fractions_intro'][0](800)
            assert result['correct_answer'].isdigit()


class TestOddEven:
    def test_low_difficulty_asks_odd_or_even(self):
        for _ in range(10):
            result = GRADE2_TEMPLATES['g2_odd_even'][0](600)
            assert result['correct_answer'] in ('odd', 'even')
