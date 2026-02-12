"""Tests for ai/local_generators.py — clock question generation."""
from ai.local_generators import (
    is_clock_node, generate_clock_question, _format_clock_time,
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
