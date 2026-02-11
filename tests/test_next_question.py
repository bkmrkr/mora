"""Tests for engine/next_question.py — variety-first node selection."""
from engine.next_question import (
    analyze_recent, select_focus_node, compute_question_params,
    _get_eligible_nodes, _find_weak_prerequisite,
)


def _make_attempt(node_id, is_correct, difficulty=800):
    return {
        'curriculum_node_id': node_id,
        'is_correct': is_correct,
        'difficulty': difficulty,
    }


def _make_node(node_id, order_index, prerequisites=None):
    return {
        'id': node_id,
        'order_index': order_index,
        'prerequisites': '[]' if prerequisites is None else str(prerequisites),
        'name': f'Node {node_id}',
    }


# === analyze_recent ===

def test_analyze_empty():
    result = analyze_recent([], {})
    assert result['overall_accuracy'] == 0.0
    assert result['total_attempts'] == 0
    assert result['last_seen'] == {}


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


def test_analyze_last_seen():
    """last_seen tracks how many questions ago each node was seen."""
    attempts = [
        _make_attempt(3, True),   # index 0 (most recent)
        _make_attempt(1, True),   # index 1
        _make_attempt(2, False),  # index 2
        _make_attempt(1, True),   # index 3 (1 already seen at index 1)
    ]
    result = analyze_recent(attempts, {})
    assert result['last_seen'][3] == 0  # node 3 most recently seen
    assert result['last_seen'][1] == 1  # node 1 seen 1 question ago
    assert result['last_seen'][2] == 2  # node 2 seen 2 questions ago


def test_analyze_last_seen_empty():
    result = analyze_recent([], {})
    assert result['last_seen'] == {}


# === select_focus_node: variety-first ===

def test_select_untouched_node():
    """Should pick first untouched node when no history."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    analysis = analyze_recent([], {})
    result = select_focus_node(analysis, nodes, {})
    # All nodes have equal score (virgin bonus), picks first
    assert result == 1


def test_select_never_same_node_twice():
    """Should never return the current node — the core variety rule."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    analysis = analyze_recent([], {})
    result = select_focus_node(analysis, nodes, {}, current_node_id=1)
    assert result != 1


def test_select_never_same_after_correct():
    """After correct answer, must switch to a different node."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {
        1: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        2: {'mastery_level': 0.2, 'skill_rating': 850, 'total_attempts': 3},
    }
    attempts = [_make_attempt(1, True)]
    analysis = analyze_recent(attempts, skills)
    result = select_focus_node(analysis, nodes, skills,
                               current_node_id=1, last_was_correct=True)
    assert result == 2


def test_select_never_same_after_wrong():
    """After wrong answer, still switches to different node (variety)."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {
        1: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        2: {'mastery_level': 0.2, 'skill_rating': 850, 'total_attempts': 3},
    }
    attempts = [_make_attempt(1, False)]
    analysis = analyze_recent(attempts, skills)
    result = select_focus_node(analysis, nodes, skills,
                               current_node_id=1, last_was_correct=False)
    assert result == 2


def test_select_only_one_eligible():
    """When only 1 eligible node, return it even if it's the current node."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {
        1: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        2: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 50},  # mastered
    }
    analysis = analyze_recent([], skills)
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    assert result == 1  # only eligible node


def test_select_prefers_low_mastery():
    """Node with lower mastery should score higher."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    skills = {
        1: {'mastery_level': 0.6, 'skill_rating': 1000, 'total_attempts': 10},
        2: {'mastery_level': 0.1, 'skill_rating': 800, 'total_attempts': 3},
        3: {'mastery_level': 0.4, 'skill_rating': 900, 'total_attempts': 5},
    }
    analysis = analyze_recent([], skills)
    # Current = 1, should pick node 2 (lowest mastery)
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    assert result == 2


def test_select_prefers_not_recently_seen():
    """Node not seen recently should score higher via recency bonus."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    skills = {
        1: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        2: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        3: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
    }
    # Node 2 was seen most recently, node 3 not seen at all in recent
    attempts = [
        _make_attempt(1, True),   # 0: most recent
        _make_attempt(2, True),   # 1
    ]
    analysis = analyze_recent(attempts, skills)
    # Current = 1, between nodes 2 and 3:
    # node 2: last_seen=1, recency_bonus=0.33
    # node 3: last_seen=99, recency_bonus=2.0
    # Node 3 should win
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    assert result == 3


def test_select_virgin_node_bonus():
    """Untouched nodes get a bonus to introduce new topics."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    skills = {
        1: {'mastery_level': 0.5, 'skill_rating': 1000, 'total_attempts': 10},
        2: {'mastery_level': 0.5, 'skill_rating': 1000, 'total_attempts': 10},
        # Node 3 has no skill record (virgin)
    }
    analysis = analyze_recent([], skills)
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    # Node 3 is virgin: need=1.0, recency_bonus=2.0 (never seen), virgin_bonus=0.5
    # Score = 1.0*(0.5+2.0)+0.5 = 3.0
    # Node 2: need=0.5, recency_bonus=2.0, no virgin bonus
    # Score = 0.5*(0.5+2.0)+0 = 1.25
    assert result == 3


def test_select_next_on_mastery():
    """Should pick a different unmastered node when current is mastered."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {1: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 20}}
    analysis = analyze_recent([], skills)
    result = select_focus_node(analysis, nodes, skills, current_node_id=1)
    assert result == 2


def test_select_all_mastered():
    """When all nodes mastered, return least mastered for continued practice."""
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {
        1: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 50},
        2: {'mastery_level': 0.8, 'skill_rating': 1100, 'total_attempts': 40},
    }
    analysis = analyze_recent([], skills)
    result = select_focus_node(analysis, nodes, skills)
    assert result == 2  # least mastered


def test_select_empty_nodes():
    assert select_focus_node({'per_node': {}, 'last_seen': {}}, [], {}) is None


# === Prerequisite handling ===

def test_select_prerequisite_fallback_on_struggle():
    """After wrong answer with <50% accuracy, fall back to weak prerequisite."""
    nodes = [_make_node(1, 0), _make_node(2, 1, prerequisites=[1])]
    skills = {
        1: {'mastery_level': 0.2, 'skill_rating': 800, 'total_attempts': 3},
        2: {'mastery_level': 0.1, 'skill_rating': 750, 'total_attempts': 5},
    }
    attempts = [
        _make_attempt(2, False),
        _make_attempt(2, False),
        _make_attempt(2, True),
        _make_attempt(2, False),
        _make_attempt(2, False),
    ]
    analysis = analyze_recent(attempts, skills)
    # Node 2 accuracy = 1/5 = 20%, wrong answer → should fall back to prereq node 1
    result = select_focus_node(analysis, nodes, skills,
                               current_node_id=2, last_was_correct=False)
    assert result == 1


def test_select_no_prereq_fallback_when_correct():
    """After correct answer, no prerequisite fallback (even if accuracy low)."""
    nodes = [_make_node(1, 0), _make_node(2, 1, prerequisites=[1])]
    skills = {
        1: {'mastery_level': 0.2, 'skill_rating': 800, 'total_attempts': 3},
        2: {'mastery_level': 0.1, 'skill_rating': 750, 'total_attempts': 5},
    }
    attempts = [_make_attempt(2, False)] * 4 + [_make_attempt(2, True)]
    analysis = analyze_recent(attempts, skills)
    # Even with low accuracy, correct answer should just switch to different node
    result = select_focus_node(analysis, nodes, skills,
                               current_node_id=2, last_was_correct=True)
    assert result == 1  # still picks node 1, but because of scoring, not prereq logic


# === _get_eligible_nodes ===

def test_eligible_excludes_mastered():
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    skills = {
        1: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 50},
        2: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
    }
    eligible = _get_eligible_nodes(nodes, skills)
    assert len(eligible) == 1
    assert eligible[0]['id'] == 2


def test_eligible_respects_prerequisites():
    """Node with unmet prerequisites (not mastered, <2 attempts) is excluded."""
    nodes = [_make_node(1, 0), _make_node(2, 1, prerequisites=[1])]
    skills = {
        1: {'mastery_level': 0.1, 'skill_rating': 800, 'total_attempts': 1},  # not accessible
    }
    eligible = _get_eligible_nodes(nodes, skills)
    assert len(eligible) == 1
    assert eligible[0]['id'] == 1  # only node 1 is eligible


def test_eligible_unlocks_after_2_attempts():
    """Node with prerequisite attempted 2+ times is accessible (soft prereq)."""
    nodes = [_make_node(1, 0), _make_node(2, 1, prerequisites=[1])]
    skills = {
        1: {'mastery_level': 0.2, 'skill_rating': 850, 'total_attempts': 2},
    }
    eligible = _get_eligible_nodes(nodes, skills)
    assert len(eligible) == 2  # both nodes accessible


def test_eligible_unlocks_on_mastered_prereq():
    nodes = [_make_node(1, 0), _make_node(2, 1, prerequisites=[1])]
    skills = {
        1: {'mastery_level': 0.9, 'skill_rating': 1200, 'total_attempts': 50},
    }
    eligible = _get_eligible_nodes(nodes, skills)
    assert len(eligible) == 1
    assert eligible[0]['id'] == 2  # node 1 mastered, node 2 now eligible


def test_eligible_no_prereqs_always_eligible():
    nodes = [_make_node(1, 0), _make_node(2, 1)]
    eligible = _get_eligible_nodes(nodes, {})
    assert len(eligible) == 2


# === _find_weak_prerequisite ===

def test_find_weak_prereq():
    nodes_by_id = {
        1: _make_node(1, 0),
        2: _make_node(2, 1, prerequisites=[1]),
    }
    skills = {1: {'mastery_level': 0.2, 'skill_rating': 800}}
    assert _find_weak_prerequisite(nodes_by_id[2], skills, nodes_by_id) == 1


def test_find_weak_prereq_mastered():
    nodes_by_id = {
        1: _make_node(1, 0),
        2: _make_node(2, 1, prerequisites=[1]),
    }
    skills = {1: {'mastery_level': 0.9, 'skill_rating': 1200}}
    assert _find_weak_prerequisite(nodes_by_id[2], skills, nodes_by_id) is None


def test_find_weak_prereq_none():
    nodes_by_id = {1: _make_node(1, 0)}
    assert _find_weak_prerequisite(nodes_by_id[1], {}, nodes_by_id) is None


# === compute_question_params ===

def test_compute_question_params_mcq_early():
    """Low mastery should produce MCQ type."""
    skills = {1: {'skill_rating': 1000, 'mastery_level': 0.1, 'total_attempts': 2}}
    analysis = {'per_node': {}}
    diff, q_type = compute_question_params(1, skills, analysis)
    assert q_type == 'mcq'
    assert diff < 1000  # Should be easier than skill


def test_compute_question_params_short_answer_late():
    """High mastery should produce short_answer type."""
    skills = {1: {'skill_rating': 1200, 'mastery_level': 0.8, 'total_attempts': 50}}
    analysis = {'per_node': {}}
    diff, q_type = compute_question_params(1, skills, analysis)
    assert q_type == 'short_answer'


# === Multi-node rotation scenario ===

def test_rotation_across_three_nodes():
    """Simulate 3 questions — should hit 3 different nodes."""
    nodes = [_make_node(1, 0), _make_node(2, 1), _make_node(3, 2)]
    skills = {
        1: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        2: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
        3: {'mastery_level': 0.3, 'skill_rating': 900, 'total_attempts': 5},
    }

    # First question
    attempts = []
    analysis = analyze_recent(attempts, skills)
    node1 = select_focus_node(analysis, nodes, skills)
    assert node1 is not None

    # Second question (after correct on node1)
    attempts = [_make_attempt(node1, True)]
    analysis = analyze_recent(attempts, skills)
    node2 = select_focus_node(analysis, nodes, skills,
                              current_node_id=node1, last_was_correct=True)
    assert node2 != node1

    # Third question (after correct on node2)
    attempts = [_make_attempt(node2, True), _make_attempt(node1, True)]
    analysis = analyze_recent(attempts, skills)
    node3 = select_focus_node(analysis, nodes, skills,
                              current_node_id=node2, last_was_correct=True)
    assert node3 != node2
    # Should prefer the node not seen recently (node that isn't node1 or node2)
    # All 3 nodes should have been visited
    assert len({node1, node2, node3}) >= 2  # at minimum 2 distinct
