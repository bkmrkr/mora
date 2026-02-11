"""Tests for engine/next_question.py."""
from engine.next_question import analyze_recent, select_focus_node, compute_question_params


def _make_attempt(node_id, is_correct, difficulty=800):
    return {
        'curriculum_node_id': node_id,
        'is_correct': is_correct,
        'difficulty': difficulty,
    }


def _make_node(node_id, order_index):
    return {
        'id': node_id,
        'order_index': order_index,
        'prerequisites': '[]',
    }


def test_analyze_empty():
    result = analyze_recent([], {})
    assert result['overall_accuracy'] == 0.0
    assert result['total_attempts'] == 0


def test_analyze_accuracy():
    attempts = [
        _make_attempt(1, True),
        _make_attempt(1, False),
        _make_attempt(1, True),
        _make_attempt(1, True),
    ]
    result = analyze_recent(attempts, {})
    assert abs(result['overall_accuracy'] - 0.75) < 0.01


def test_analyze_per_node():
    attempts = [
        _make_attempt(1, True),
        _make_attempt(2, False),
        _make_attempt(1, True),
    ]
    result = analyze_recent(attempts, {})
    assert result['per_node'][1]['accuracy'] == 1.0
    assert result['per_node'][2]['accuracy'] == 0.0


def test_select_untouched_node():
    """Should pick first untouched node when no history."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    result = select_focus_node({'per_node': {}}, nodes, {})
    assert result == 1


def test_select_next_on_mastery():
    """Should advance to next node when current is mastered."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {1: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 20}}
    analysis = {
        'per_node': {1: {'accuracy': 0.95, 'results': [True]*10, 'count': 10, 'correct': 10}},
    }
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    assert result == 2


def test_compute_question_params_mcq_early():
    """Low mastery should produce MCQ type."""
    skills = {1: {'skill_rating': 1000, 'mastery_level': 0.1, 'total_attempts': 2}}
    analysis = {'per_node': {}}
    diff, q_type = compute_question_params(1, skills, analysis)
    assert q_type == 'mcq'
    assert diff < 1000  # Should be easier than skill


def test_compute_question_params_problem_late():
    """High mastery should produce problem type."""
    skills = {1: {'skill_rating': 1200, 'mastery_level': 0.7, 'total_attempts': 50}}
    analysis = {'per_node': {}}
    diff, q_type = compute_question_params(1, skills, analysis)
    assert q_type == 'problem'
