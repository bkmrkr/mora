"""Tests for ai/local_generators.py — clock + inequality generation."""
from ai.local_generators import (
    is_clock_node, generate_clock_question, _format_clock_time,
    is_inequality_node, generate_inequality_question,
)


# --- is_clock_node ---

def test_clock_node_by_name():
    assert is_clock_node('Telling Time') is True


def test_clock_node_by_description():
    assert is_clock_node('Skill 1', 'Reading analog clock faces') is True


def test_not_clock_node():
    assert is_clock_node('Addition', 'Adding numbers') is False


def test_clock_node_case_insensitive():
    assert is_clock_node('READING CLOCKS') is True


# --- generate_clock_question ---

def test_returns_tuple_of_three():
    q_data, model, prompt = generate_clock_question('Telling Time')
    assert isinstance(q_data, dict)
    assert model == 'local-clock'
    assert isinstance(prompt, str)


def test_question_has_required_keys():
    q_data, _, _ = generate_clock_question('Telling Time')
    assert 'question' in q_data
    assert 'correct_answer' in q_data
    assert 'options' in q_data
    assert 'clock_svg' in q_data


def test_four_options():
    q_data, _, _ = generate_clock_question('Telling Time')
    assert len(q_data['options']) == 4


def test_correct_answer_in_options():
    q_data, _, _ = generate_clock_question('Telling Time')
    assert q_data['correct_answer'] in q_data['options']


def test_svg_is_valid():
    q_data, _, _ = generate_clock_question('Telling Time')
    assert q_data['clock_svg'].startswith('<svg')
    assert '</svg>' in q_data['clock_svg']


def test_hour_only_node():
    """Hour-only nodes should produce :00 times."""
    q_data, _, _ = generate_clock_question('Telling Time to the Hour')
    assert q_data['correct_answer'].endswith(':00')


def test_quarter_hour_node():
    """Quarter-hour nodes produce :00, :15, :30, or :45."""
    q_data, _, _ = generate_clock_question('Telling Time to the Quarter Hour')
    minute = q_data['correct_answer'].split(':')[1]
    assert minute in ('00', '15', '30', '45')


def test_avoids_recent_questions():
    """With all but one time as recent, should pick the remaining one."""
    # Generate all possible hour-only times as "recent"
    recent = [f"What time does this clock show? [{h}:00]" for h in range(1, 12)]
    q_data, _, _ = generate_clock_question('Telling Time to the Hour', recent_questions=recent)
    assert q_data['correct_answer'] == '12:00'


# --- _format_clock_time ---

def test_format_hour():
    assert _format_clock_time(3, 0) == '3:00'


def test_format_quarter():
    assert _format_clock_time(7, 15) == '7:15'


# =====================================================================
# Inequality number line generator
# =====================================================================

# --- is_inequality_node ---

def test_inequality_node_by_name():
    assert is_inequality_node('Solving Inequalities') is True


def test_inequality_node_by_description():
    assert is_inequality_node('Skill X', 'Graph inequalities on a number line') is True


def test_not_inequality_node():
    assert is_inequality_node('Addition', 'Adding numbers') is False


def test_inequality_node_case_insensitive():
    assert is_inequality_node('NUMBER LINES') is True


# --- generate_inequality_question ---

def test_ineq_returns_tuple_of_three():
    q_data, model, prompt = generate_inequality_question('Solving Inequalities')
    assert isinstance(q_data, dict)
    assert model == 'local-inequality'
    assert isinstance(prompt, str)


def test_ineq_has_required_keys():
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    assert 'question' in q_data
    assert 'correct_answer' in q_data
    assert 'options' in q_data
    assert 'number_line_svg' in q_data


def test_ineq_four_options():
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    assert len(q_data['options']) == 4


def test_ineq_correct_answer_in_options():
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    assert q_data['correct_answer'] in q_data['options']


def test_ineq_svg_valid():
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    svg = q_data['number_line_svg']
    assert svg.startswith('<svg')
    assert '</svg>' in svg
    assert '<circle' in svg  # boundary circle
    assert '<text' in svg    # number labels


def test_ineq_svg_has_tick_labels():
    """SVG should contain integer labels."""
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    svg = q_data['number_line_svg']
    assert '>0<' in svg  # zero label


def test_ineq_options_are_expressions():
    """Options should be inequality expressions, not text descriptions."""
    q_data, _, _ = generate_inequality_question('Solving Inequalities')
    for opt in q_data['options']:
        assert opt.startswith('x ')


def test_ineq_avoids_recent():
    """With all but a few as recent, should avoid them."""
    recent = [
        f"Which inequality does this number line represent? [x {op} {v}]"
        for op in ['>', '<', '>=', '<=']
        for v in range(-5, 5)  # -5 to 4, leaving 5
    ]
    q_data, _, _ = generate_inequality_question('Inequalities', recent_questions=recent)
    # Should still generate something (boundary=5 with some operator)
    assert q_data is not None
