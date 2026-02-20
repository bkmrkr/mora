"""Edge case and regression tests for question templates.

These tests verify:
1. All templates produce valid output structure
2. Options don't include duplicate answers
3. All 4 options are unique
4. Answer is always in the options
"""
import pytest
import random
from curriculum.templates import grade1, grade2, grade3, grade4
from curriculum.templates.common import make_options, arithmetic_distractors


class TestGrade1Templates:
    """Test Grade 1 templates for edge cases."""

    @pytest.mark.parametrize("elo", [500, 700, 900])
    def test_addition_within_10(self, elo):
        """Verify addition within 10 produces valid output."""
        for _ in range(20):
            result = grade1.addition_within_10(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [500, 700, 900])
    def test_subtraction_within_10(self, elo):
        """Verify subtraction within 10 produces valid output."""
        for _ in range(20):
            result = grade1.subtraction_within_10(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [500, 700, 900])
    def test_addition_within_20(self, elo):
        """Verify addition within 20 produces valid output."""
        for _ in range(20):
            result = grade1.addition_within_20(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [500, 700, 900])
    def test_subtraction_within_20(self, elo):
        """Verify subtraction within 20 produces valid output."""
        for _ in range(20):
            result = grade1.subtraction_within_20(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_place_value(self, elo):
        """Verify place value produces valid output."""
        for _ in range(20):
            result = grade1.place_value(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_counting(self, elo):
        """Verify counting produces valid output."""
        for _ in range(30):
            result = grade1.counting_to_120(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 950])
    def test_comparing_numbers(self, elo):
        """Verify comparing numbers produces valid output."""
        for _ in range(20):
            result = grade1.comparing_numbers(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 950])
    def test_telling_time_hour(self, elo):
        """Verify telling time produces valid output."""
        for _ in range(20):
            result = grade1.telling_time_hour(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4
            assert 'clock_hour' in result

    @pytest.mark.parametrize("elo", [600, 800, 950])
    def test_basic_shapes(self, elo):
        """Verify shapes produces valid output."""
        for _ in range(30):
            result = grade1.basic_shapes(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 950])
    def test_word_problems_add_sub(self, elo):
        """Verify word problems produce valid output."""
        for _ in range(30):
            result = grade1.word_problems_add_sub(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4


class TestGrade2Templates:
    """Test Grade 2 templates for edge cases."""

    @pytest.mark.parametrize("elo", [700, 850, 1000])
    def test_add_sub_within_100(self, elo):
        """Verify add/sub within 100 produces valid output."""
        for _ in range(30):
            result = grade2.add_sub_within_100(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1000])
    def test_add_sub_within_1000(self, elo):
        """Verify add/sub within 1000 produces valid output."""
        for _ in range(30):
            result = grade2.add_sub_within_1000(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_intro_multiply(self, elo):
        """Verify intro multiplication produces valid output."""
        for _ in range(30):
            result = grade2.intro_multiply(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_money(self, elo):
        """Verify money produces valid output."""
        for _ in range(30):
            result = grade2.money(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_telling_time_5min(self, elo):
        """Verify 5-minute time produces valid output."""
        for _ in range(20):
            result = grade2.telling_time_5min(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4
            assert 'clock_hour' in result

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_measurement_length(self, elo):
        """Verify measurement produces valid output."""
        for _ in range(30):
            result = grade2.measurement_length(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1000])
    def test_fractions_intro(self, elo):
        """Verify fractions intro produces valid output."""
        for _ in range(30):
            result = grade2.fractions_intro(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1000])
    def test_comparing_3digit(self, elo):
        """Verify 3-digit comparison produces valid output."""
        for _ in range(20):
            result = grade2.comparing_3digit(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1000])
    def test_two_step_word(self, elo):
        """Verify two-step word problems produce valid output."""
        for _ in range(30):
            result = grade2.two_step_word(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [600, 800, 1000])
    def test_odd_even(self, elo):
        """Verify odd/even produces valid output."""
        for _ in range(30):
            result = grade2.odd_even(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4


class TestGrade3Templates:
    """Test Grade 3 templates for edge cases."""

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_multiplication_facts(self, elo):
        """Verify multiplication facts produce valid output."""
        for _ in range(30):
            result = grade3.multiplication_facts(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_division_facts(self, elo):
        """Verify division facts produce valid output."""
        for _ in range(30):
            result = grade3.division_facts(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_multi_digit_multiply(self, elo):
        """Verify multi-digit multiplication produces valid output."""
        for _ in range(30):
            result = grade3.multi_digit_multiply(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_area_perimeter(self, elo):
        """Verify area/perimeter produces valid output."""
        for _ in range(30):
            result = grade3.area_perimeter(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_fraction_compare(self, elo):
        """Verify fraction comparison produces valid output."""
        for _ in range(30):
            result = grade3.fraction_compare(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_fraction_add_sub(self, elo):
        """Verify fraction add/sub produces valid output."""
        for _ in range(30):
            result = grade3.fraction_add_sub(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_rounding(self, elo):
        """Verify rounding produces valid output."""
        for _ in range(30):
            result = grade3.rounding(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_mult_div_word(self, elo):
        """Verify mult/div word problems produce valid output."""
        for _ in range(30):
            result = grade3.mult_div_word_problems(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_elapsed_time(self, elo):
        """Verify elapsed time produces valid output."""
        for _ in range(30):
            result = grade3.elapsed_time(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1100])
    def test_data_interpretation(self, elo):
        """Verify data interpretation produces valid output."""
        for _ in range(30):
            result = grade3.data_interpretation(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4


class TestGrade4Templates:
    """Test Grade 4 templates for edge cases."""

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_multi_digit_multiply(self, elo):
        """Verify 2-digit multiplication produces valid output."""
        for _ in range(30):
            result = grade4.multi_digit_multiply(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_long_division(self, elo):
        """Verify long division produces valid output."""
        for _ in range(30):
            result = grade4.long_division(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_fraction_ops(self, elo):
        """Verify fraction operations produce valid output."""
        for _ in range(30):
            result = grade4.fraction_ops(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_decimal_place_value(self, elo):
        """Verify decimal place value produces valid output."""
        for _ in range(30):
            result = grade4.decimal_place_value(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_decimal_add_sub(self, elo):
        """Verify decimal add/sub produces valid output."""
        for _ in range(30):
            result = grade4.decimal_add_sub(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_angles(self, elo):
        """Verify angles produces valid output."""
        for _ in range(30):
            result = grade4.angles(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_geometry_lines(self, elo):
        """Verify geometry lines produces valid output."""
        for _ in range(30):
            result = grade4.geometry_lines(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_factors_multiples(self, elo):
        """Verify factors and multiples produce valid output."""
        for _ in range(30):
            result = grade4.factors_multiples(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_multi_step_word(self, elo):
        """Verify multi-step word problems produce valid output."""
        for _ in range(30):
            result = grade4.multi_step_word(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4

    @pytest.mark.parametrize("elo", [700, 850, 1200])
    def test_equivalent_fractions(self, elo):
        """Verify equivalent fractions produce valid output."""
        for _ in range(30):
            result = grade4.equivalent_fractions(elo)
            assert result['correct_answer'] in result['options']
            assert len(set(result['options'])) == 4


class TestMakeOptions:
    """Test make_options utility for edge cases."""

    def test_integer_no_duplicates(self):
        """Verify no duplicate options for integers."""
        for _ in range(100):
            correct = random.randint(1, 100)
            distractors = [str(correct + i) for i in [-3, -2, -1, 1, 2, 3]]
            options = make_options(str(correct), distractors)
            assert len(set(options)) == 4
            assert str(correct) in options

    def test_fraction_no_duplicates(self):
        """Verify no duplicate options for fractions."""
        for _ in range(50):
            correct = f"{random.randint(1, 5)}/{random.randint(2, 8)}"
            distractors = ["1/2", "3/4", "1/3"]
            options = make_options(correct, distractors)
            assert len(set(options)) == 4

    def test_decimal_no_duplicates(self):
        """Verify no duplicate options for decimals."""
        for _ in range(50):
            correct = round(random.random() * 10, 2)
            distractors = [str(round(correct + 0.1, 2)), str(round(correct - 0.1, 2))]
            options = make_options(str(correct), distractors)
            assert len(set(options)) == 4

    def test_small_number_no_duplicates(self):
        """Verify no duplicates for small numbers (common bug)."""
        for _ in range(50):
            correct = random.randint(1, 5)
            distractors = [str(correct + i) for i in [-2, -1, 1, 2]]
            options = make_options(str(correct), distractors)
            assert len(set(options)) == 4


class TestArithmeticDistractors:
    """Test arithmetic_distractors for correctness."""

    def test_addition_distractors(self):
        """Verify addition distractors don't include correct answer."""
        for _ in range(50):
            answer = random.randint(1, 20)
            a, b = random.randint(1, 10), random.randint(1, 10)
            dist = arithmetic_distractors(answer, a, b, op='+')
            assert str(answer) not in dist

    def test_subtraction_distractors(self):
        """Verify subtraction distractors don't include correct answer."""
        for _ in range(50):
            answer = random.randint(1, 20)
            a, b = random.randint(5, 25), random.randint(1, 5)
            dist = arithmetic_distractors(answer, a, b, op='-')
            assert str(answer) not in dist

    def test_multiplication_distractors(self):
        """Verify multiplication distractors don't include correct answer."""
        for _ in range(50):
            answer = random.randint(1, 50)
            a, b = random.randint(2, 10), random.randint(2, 10)
            dist = arithmetic_distractors(answer, a, b, op='*')
            assert str(answer) not in dist

    def test_division_distractors(self):
        """Verify division distractors don't include correct answer."""
        for _ in range(50):
            answer = random.randint(1, 20)
            a, b = answer * random.randint(2, 5), answer
            dist = arithmetic_distractors(answer, a, b, op='/')
            assert str(answer) not in dist

    def test_no_negative_answers(self):
        """Verify distractors never produce negative answers."""
        for _ in range(100):
            answer = random.randint(0, 10)
            a, b = random.randint(1, 10), random.randint(1, 10)
            for op in ['+', '-', '*', '/']:
                dist = arithmetic_distractors(answer, a, b, op=op)
                for d in dist:
                    assert int(d) >= 0, f"Got negative distractor: {d}"


class TestTemplateRegistry:
    """Test that all templates are properly registered."""

    def test_grade1_all_registered(self):
        """Verify all Grade 1 templates are registered."""
        expected = [
            'g1_add_10', 'g1_sub_10', 'g1_add_20', 'g1_sub_20',
            'g1_place_value', 'g1_counting', 'g1_comparing',
            'g1_time', 'g1_shapes', 'g1_word_problems'
        ]
        for skill_id in expected:
            assert skill_id in grade1.GRADE1_TEMPLATES
            assert len(grade1.GRADE1_TEMPLATES[skill_id]) > 0

    def test_grade2_all_registered(self):
        """Verify all Grade 2 templates are registered."""
        expected = [
            'g2_add_sub_100', 'g2_add_sub_1000', 'g2_intro_multiply',
            'g2_money', 'g2_time', 'g2_measurement', 'g2_fractions_intro',
            'g2_comparing_3digit', 'g2_two_step', 'g2_odd_even'
        ]
        for skill_id in expected:
            assert skill_id in grade2.GRADE2_TEMPLATES
            assert len(grade2.GRADE2_TEMPLATES[skill_id]) > 0

    def test_grade3_all_registered(self):
        """Verify all Grade 3 templates are registered."""
        expected = [
            'g3_mult_facts', 'g3_div_facts', 'g3_multi_digit_mult',
            'g3_area_perimeter', 'g3_fraction_compare', 'g3_fraction_add_sub',
            'g3_rounding', 'g3_mult_div_word', 'g3_elapsed_time', 'g3_data'
        ]
        for skill_id in expected:
            assert skill_id in grade3.GRADE3_TEMPLATES
            assert len(grade3.GRADE3_TEMPLATES[skill_id]) > 0

    def test_grade4_all_registered(self):
        """Verify all Grade 4 templates are registered."""
        expected = [
            'g4_multi_digit_mult', 'g4_long_division', 'g4_fraction_ops',
            'g4_decimal_place_value', 'g4_decimal_add_sub', 'g4_angles',
            'g4_geometry', 'g4_factors_multiples', 'g4_multi_step_word',
            'g4_equivalent_fractions'
        ]
        for skill_id in expected:
            assert skill_id in grade4.GRADE4_TEMPLATES
            assert len(grade4.GRADE4_TEMPLATES[skill_id]) > 0

    def test_all_templates_produce_valid_output(self):
        """Verify every template produces valid output structure."""
        all_templates = [
            (grade1.GRADE1_TEMPLATES, grade1),
            (grade2.GRADE2_TEMPLATES, grade2),
            (grade3.GRADE3_TEMPLATES, grade3),
            (grade4.GRADE4_TEMPLATES, grade4),
        ]
        for templates, grade_mod in all_templates:
            for skill_id, template_funcs in templates.items():
                for template_func in template_funcs:
                    for elo in [600, 800, 1000]:
                        result = template_func(elo)
                        # Verify required fields
                        assert 'skill_id' in result, f"Missing skill_id in {skill_id}"
                        assert 'question' in result, f"Missing question in {skill_id}"
                        assert 'correct_answer' in result, f"Missing correct_answer in {skill_id}"
                        assert 'options' in result, f"Missing options in {skill_id}"
                        assert 'explanation' in result, f"Missing explanation in {skill_id}"
                        assert 'template_id' in result, f"Missing template_id in {skill_id}"
                        assert 'difficulty' in result, f"Missing difficulty in {skill_id}"
                        # Verify options
                        assert len(result['options']) == 4, f"Expected 4 options in {skill_id}, got {len(result['options'])}"
                        assert len(set(result['options'])) == 4, f"Duplicate options in {skill_id}"
                        assert result['correct_answer'] in result['options'], f"Answer not in options for {skill_id}"
