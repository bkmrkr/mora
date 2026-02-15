"""Tests for grade 1 question templates."""
import json

from curriculum.templates.grade1 import GRADE1_TEMPLATES


REQUIRED_KEYS = {'skill_id', 'question', 'correct_answer', 'options', 'explanation', 'template_id', 'difficulty'}


class TestAllGrade1Templates:
    """Run structural tests on every grade 1 template."""

    def test_all_skills_have_templates(self):
        expected = {
            'g1_add_10', 'g1_sub_10', 'g1_add_20', 'g1_sub_20',
            'g1_place_value', 'g1_counting', 'g1_comparing',
            'g1_time', 'g1_shapes', 'g1_word_problems',
        }
        assert set(GRADE1_TEMPLATES.keys()) == expected

    def test_each_template_returns_valid_dict(self):
        """Every template function must return a dict with all required keys."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                for elo in [500, 700, 900, 1100]:
                    result = template_fn(elo)
                    missing = REQUIRED_KEYS - set(result.keys())
                    assert not missing, \
                        f"{skill_id} at ELO {elo} missing: {missing}"

    def test_correct_answer_in_options(self):
        """The correct answer must always be in the options list."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                for elo in [500, 700, 900, 1100]:
                    result = template_fn(elo)
                    assert result['correct_answer'] in result['options'], \
                        f"{skill_id} ELO {elo}: answer '{result['correct_answer']}' not in {result['options']}"

    def test_four_options(self):
        """Each question should have exactly 4 options."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                for elo in [600, 800, 1000]:
                    result = template_fn(elo)
                    assert len(result['options']) == 4, \
                        f"{skill_id} ELO {elo}: got {len(result['options'])} options"

    def test_options_are_unique(self):
        """No duplicate options."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                for _ in range(5):  # run multiple times due to randomness
                    result = template_fn(800)
                    opts = result['options']
                    assert len(opts) == len(set(opts)), \
                        f"{skill_id}: duplicate options {opts}"

    def test_skill_id_matches(self):
        """The returned skill_id must match the registry key."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                result = template_fn(800)
                assert result['skill_id'] == skill_id

    def test_variety_across_runs(self):
        """Multiple calls should produce different questions (randomness works)."""
        for skill_id, templates in GRADE1_TEMPLATES.items():
            for template_fn in templates:
                results = [template_fn(800) for _ in range(20)]
                # For clock questions, variety is in the answer (different times)
                if results[0].get('clock_hour') is not None:
                    answers = {r['correct_answer'] for r in results}
                    assert len(answers) > 1, \
                        f"{skill_id}: same answer generated 20 times"
                else:
                    questions = {r['question'] for r in results}
                    assert len(questions) > 1, \
                        f"{skill_id}: same question generated 20 times"


class TestAdditionWithin10:
    def test_sum_within_10(self):
        from curriculum.templates.grade1 import addition_within_10
        for _ in range(50):
            result = addition_within_10(800)
            parts = result['question'].replace('?', '').split('+')
            a, b = int(parts[0].strip().split()[-1]), int(parts[1].strip())
            assert a + b <= 10
            assert a >= 0 and b >= 0

    def test_answer_is_correct(self):
        from curriculum.templates.grade1 import addition_within_10
        for _ in range(50):
            result = addition_within_10(800)
            parts = result['question'].replace('?', '').split('+')
            a, b = int(parts[0].strip().split()[-1]), int(parts[1].strip())
            assert result['correct_answer'] == str(a + b)


class TestSubtractionWithin10:
    def test_no_negatives(self):
        from curriculum.templates.grade1 import subtraction_within_10
        for _ in range(50):
            result = subtraction_within_10(800)
            assert int(result['correct_answer']) >= 0


class TestPlaceValue:
    def test_answer_is_valid_digit(self):
        from curriculum.templates.grade1 import place_value
        for _ in range(50):
            result = place_value(800)
            ans = int(result['correct_answer'])
            assert 0 <= ans <= 9


class TestCountingTo120:
    def test_low_difficulty_next_number(self):
        from curriculum.templates.grade1 import counting_to_120
        for _ in range(20):
            result = counting_to_120(600)
            assert 'after' in result['question']

    def test_high_difficulty_skip_counting(self):
        from curriculum.templates.grade1 import counting_to_120
        for _ in range(20):
            result = counting_to_120(900)
            assert 'Count by' in result['question'] or 'before' in result['question']


class TestShapes:
    def test_valid_shapes(self):
        from curriculum.templates.grade1 import basic_shapes
        valid_names = {'triangle', 'square', 'rectangle', 'circle', 'hexagon'}
        for _ in range(30):
            result = basic_shapes(800)
            # Either the answer is a shape name or a side count
            if result['correct_answer'] in valid_names:
                pass  # sides_to_name variant
            else:
                assert result['correct_answer'].isdigit()  # name_to_sides variant


class TestWordProblems:
    def test_answers_non_negative(self):
        from curriculum.templates.grade1 import word_problems_add_sub
        for _ in range(50):
            result = word_problems_add_sub(800)
            assert int(result['correct_answer']) >= 0
