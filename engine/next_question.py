"""Next-question selection — variety-first approach.

Algorithm:
1. Analyze last 30 attempts → per-node accuracy, trend, recency
2. Select focus node: NEVER same node twice, score by need + recency
3. Compute target difficulty from ELO + recent calibration
"""
import json

from engine import elo
from engine.difficulty import calibrate_from_recent

# Nodes that require visual aids (images, physical objects, charts) and can't
# be answered in text-only format. Skipped until image generators are added.
# Clock nodes are NOT here — they already have an SVG generator.
VISUAL_REQUIRED_NODES = {
    'Comparing and Ordering Lengths',
    'Measuring Length with Units',
    'Organizing and Reading Data',
    'Interpreting Data and Answering Questions',
    'Composing Shapes',
    'Partitioning into Equal Shares',
}


def analyze_recent(recent_attempts, student_skills):
    """Analyze last 30 attempts for per-node stats, overall accuracy, recency.

    Args:
        recent_attempts: list of dicts with keys: curriculum_node_id, is_correct, difficulty
            Ordered newest-first.
        student_skills: dict of {node_id: student_skill_row}

    Returns dict with overall_accuracy, per_node stats, improvement_trend, last_seen.
    """
    if not recent_attempts:
        return {
            'overall_accuracy': 0.0,
            'per_node': {},
            'improvement_trend': 'stable',
            'total_attempts': 0,
            'last_seen': {},
        }

    total_correct = sum(1 for a in recent_attempts if a['is_correct'])
    overall_accuracy = total_correct / len(recent_attempts)

    # Per-node stats
    per_node = {}
    for a in recent_attempts:
        nid = a['curriculum_node_id']
        if nid not in per_node:
            per_node[nid] = {'results': [], 'count': 0, 'correct': 0}
        is_correct = bool(a['is_correct'])
        per_node[nid]['results'].append(is_correct)
        per_node[nid]['count'] += 1
        if is_correct:
            per_node[nid]['correct'] += 1

    for nid, stats in per_node.items():
        stats['accuracy'] = stats['correct'] / stats['count'] if stats['count'] else 0

    # Improvement trend: compare first half vs second half
    half = len(recent_attempts) // 2
    if half >= 3:
        first_half = sum(1 for a in recent_attempts[half:] if a['is_correct']) / (len(recent_attempts) - half)
        second_half = sum(1 for a in recent_attempts[:half] if a['is_correct']) / half
        if second_half - first_half > 0.1:
            trend = 'improving'
        elif first_half - second_half > 0.1:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'

    # Recency: how many questions ago was each node last seen?
    # Index 0 = most recent attempt
    last_seen = {}
    for i, a in enumerate(recent_attempts):
        nid = a.get('curriculum_node_id')
        if nid and nid not in last_seen:
            last_seen[nid] = i

    return {
        'overall_accuracy': overall_accuracy,
        'per_node': per_node,
        'improvement_trend': trend,
        'total_attempts': len(recent_attempts),
        'last_seen': last_seen,
    }


def select_focus_node(recent_analysis, curriculum_nodes, student_skills,
                      current_node_id=None, last_was_correct=None):
    """Pick the curriculum node for the next question — variety-first.

    Core rule: NEVER repeat the same node consecutively.
    Scores candidates by need (low mastery) and recency (not seen recently).

    Args:
        recent_analysis: output from analyze_recent()
        curriculum_nodes: list of node dicts
        student_skills: dict of {node_id: skill_row}
        current_node_id: the node of the question just answered
        last_was_correct: whether the last answer was correct (None for first question)

    Returns node_id or None.
    """
    if not curriculum_nodes:
        return None

    nodes_by_id = {n['id']: n for n in curriculum_nodes}
    per_node = recent_analysis.get('per_node', {})
    last_seen = recent_analysis.get('last_seen', {})

    # Build eligible pool: unmastered nodes with accessible prerequisites
    eligible = _get_eligible_nodes(curriculum_nodes, student_skills)

    if not eligible:
        # All mastered — return least mastered for continued practice
        return _least_mastered_id(curriculum_nodes, student_skills)

    # After wrong answer with low accuracy: check for weak prerequisite
    if last_was_correct is False and current_node_id and current_node_id in nodes_by_id:
        node_stats = per_node.get(current_node_id)
        if node_stats and node_stats['accuracy'] < 0.50:
            prereq = _find_weak_prerequisite(
                nodes_by_id[current_node_id], student_skills, nodes_by_id
            )
            if prereq and prereq != current_node_id:
                return prereq

    # Hard rule: exclude current node (never same node twice in a row)
    candidates = [n for n in eligible if n['id'] != current_node_id]
    if not candidates:
        candidates = eligible  # only 1 eligible node — use it

    # Score candidates by need + recency + virgin bonus
    best_id, best_score = None, -1.0
    for node in candidates:
        skill = student_skills.get(node['id'], {})
        mastery = skill.get('mastery_level', 0.0)
        need = 1.0 - mastery

        # Recency: how many questions since last asked?
        recency = last_seen.get(node['id'], 99)
        recency_bonus = min(recency / 3.0, 2.0)

        # Virgin node bonus: introduce new topics
        attempts = skill.get('total_attempts', 0)
        virgin_bonus = 0.5 if attempts == 0 else 0.0

        score = need * (0.5 + recency_bonus) + virgin_bonus

        if score > best_score:
            best_score = score
            best_id = node['id']

    return best_id


def _get_eligible_nodes(curriculum_nodes, student_skills):
    """Get unmastered nodes whose prerequisites are accessible.

    Prerequisites are "accessible" if mastered OR attempted 2+ times.
    This allows variety without hard-locking behind sequential mastery.
    """
    eligible = []
    node_ids = {n['id'] for n in curriculum_nodes}

    for node in curriculum_nodes:
        # Skip nodes that require visual aids we can't generate yet
        if node.get('name') in VISUAL_REQUIRED_NODES:
            continue

        skill = student_skills.get(node['id'], {})
        if elo.is_mastered(skill.get('mastery_level', 0.0)):
            continue

        prereqs = _get_prerequisite_ids(node)
        if prereqs:
            accessible = all(
                elo.is_mastered(student_skills.get(pid, {}).get('mastery_level', 0.0))
                or student_skills.get(pid, {}).get('total_attempts', 0) >= 2
                for pid in prereqs
                if pid in node_ids
            )
            if not accessible:
                continue

        eligible.append(node)
    return eligible


def _find_weak_prerequisite(node, student_skills, nodes_by_id):
    """Find an unmastered prerequisite of the given node."""
    prereqs = _get_prerequisite_ids(node)
    for pid in prereqs:
        if pid in nodes_by_id:
            p_skill = student_skills.get(pid, {})
            if not elo.is_mastered(p_skill.get('mastery_level', 0.0)):
                return pid
    return None


def _least_mastered_id(curriculum_nodes, student_skills):
    """Return the node_id with the lowest mastery level."""
    least_id, least_mastery = None, 1.0
    for node in curriculum_nodes:
        skill = student_skills.get(node['id'], {})
        m = skill.get('mastery_level', 0.0)
        if m < least_mastery:
            least_mastery = m
            least_id = node['id']
    return least_id


def compute_question_params(focus_node_id, student_skills, recent_analysis):
    """Compute target difficulty and question type for the focus node.

    Returns (target_difficulty, question_type).
    """
    skill = student_skills.get(focus_node_id, {})
    total_attempts = skill.get('total_attempts', 0)

    # Warm-start: for untouched nodes, use the student's proven level
    # from other nodes instead of the default 800. This prevents
    # resetting to easy questions when advancing through topics.
    if total_attempts == 0:
        rated = [s['skill_rating'] for s in student_skills.values()
                 if s.get('total_attempts', 0) >= 3]
        skill_rating = sum(rated) / len(rated) if rated else skill.get('skill_rating', 800.0)
    else:
        skill_rating = skill.get('skill_rating', 800.0)

    base_target = elo.target_difficulty(skill_rating)

    # Adjust based on recent performance.
    # Prefer per-node stats, but fall back to overall accuracy when
    # per-node data is insufficient (e.g., just advanced to a new node).
    node_stats = recent_analysis.get('per_node', {}).get(focus_node_id)
    if node_stats and len(node_stats['results']) >= 3:
        adjusted = calibrate_from_recent(base_target, node_stats['results'])
    elif recent_analysis.get('total_attempts', 0) >= 3:
        # Use all recent results across nodes for calibration
        all_results = []
        for ns in recent_analysis['per_node'].values():
            all_results.extend(ns['results'])
        adjusted = calibrate_from_recent(base_target, all_results)
    else:
        adjusted = base_target

    # Question type: mostly MCQ (easier for young kids), short_answer only when mastered
    mastery = skill.get('mastery_level', 0.0)
    if mastery < 0.7:
        q_type = 'mcq'
    else:
        q_type = 'short_answer'

    return adjusted, q_type


def _get_prerequisite_ids(node):
    """Parse prerequisites JSON field."""
    prereqs = node.get('prerequisites', '[]')
    if isinstance(prereqs, str):
        try:
            return json.loads(prereqs)
        except (json.JSONDecodeError, TypeError):
            return []
    return prereqs if isinstance(prereqs, list) else []
