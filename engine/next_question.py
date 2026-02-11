"""Next-question selection based on last-30 analysis.

Algorithm:
1. Analyze last 30 attempts → per-node accuracy, trend
2. Select focus node: current if 60-90%, prerequisite if <60%, next if mastered
3. Compute target difficulty from ELO + recent calibration
"""
import json

from engine import elo
from engine.difficulty import calibrate_from_recent


def analyze_recent(recent_attempts, student_skills):
    """Analyze last 30 attempts for per-node stats and overall accuracy.

    Args:
        recent_attempts: list of dicts with keys: curriculum_node_id, is_correct, difficulty
        student_skills: dict of {node_id: student_skill_row}

    Returns dict with overall_accuracy, per_node stats, improvement_trend.
    """
    if not recent_attempts:
        return {
            'overall_accuracy': 0.0,
            'per_node': {},
            'improvement_trend': 'stable',
            'total_attempts': 0,
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

    return {
        'overall_accuracy': overall_accuracy,
        'per_node': per_node,
        'improvement_trend': trend,
        'total_attempts': len(recent_attempts),
    }


def select_focus_node(recent_analysis, curriculum_nodes, student_skills,
                      current_node_id=None):
    """Pick the curriculum node for the next question.

    Priority:
    1. Current node if accuracy in 60-90% range (sweet spot)
    2. Prerequisites of current node if struggling (<60%)
    3. Next node in order if current is mastered
    4. Weakest recently-practiced node
    5. Next untouched node in curriculum order

    Returns node_id or None.
    """
    if not curriculum_nodes:
        return None

    per_node = recent_analysis.get('per_node', {})
    nodes_by_id = {n['id']: n for n in curriculum_nodes}

    # If we have a current node, check its performance
    if current_node_id and current_node_id in nodes_by_id:
        node_stats = per_node.get(current_node_id)
        skill = student_skills.get(current_node_id, {})
        mastery = skill.get('mastery_level', 0.0)

        if node_stats:
            acc = node_stats['accuracy']
            # Sweet spot: keep going
            if 0.60 <= acc <= 0.90 and not elo.is_mastered(mastery):
                return current_node_id

            # Struggling: fall back to prerequisites
            if acc < 0.60:
                prereqs = _get_prerequisite_ids(nodes_by_id[current_node_id])
                for pid in prereqs:
                    if pid in nodes_by_id:
                        p_skill = student_skills.get(pid, {})
                        if not elo.is_mastered(p_skill.get('mastery_level', 0.0)):
                            return pid

            # Mastered or too easy: advance
            if elo.is_mastered(mastery) or acc > 0.90:
                next_node = _next_in_order(curriculum_nodes, current_node_id, student_skills)
                if next_node:
                    return next_node

    # Weakest recently-practiced node (not mastered)
    weakest_id, weakest_acc = None, 1.0
    for nid, stats in per_node.items():
        if nid in nodes_by_id:
            skill = student_skills.get(nid, {})
            if not elo.is_mastered(skill.get('mastery_level', 0.0)):
                if stats['accuracy'] < weakest_acc:
                    weakest_acc = stats['accuracy']
                    weakest_id = nid
    if weakest_id:
        return weakest_id

    # Next untouched node in curriculum order
    for node in curriculum_nodes:
        if node['id'] not in student_skills or student_skills[node['id']].get('total_attempts', 0) == 0:
            return node['id']

    # All nodes touched — pick least mastered
    least_mastered_id, least_mastery = None, 1.0
    for node in curriculum_nodes:
        skill = student_skills.get(node['id'], {})
        m = skill.get('mastery_level', 0.0)
        if m < least_mastery:
            least_mastery = m
            least_mastered_id = node['id']

    return least_mastered_id


def compute_question_params(focus_node_id, student_skills, recent_analysis):
    """Compute target difficulty and question type for the focus node.

    Returns (target_difficulty, question_type).
    """
    skill = student_skills.get(focus_node_id, {})
    skill_rating = skill.get('skill_rating', 1000.0)

    base_target = elo.target_difficulty(skill_rating)

    # Adjust based on recent performance on this node
    node_stats = recent_analysis.get('per_node', {}).get(focus_node_id)
    if node_stats and node_stats['results']:
        adjusted = calibrate_from_recent(base_target, node_stats['results'])
    else:
        adjusted = base_target

    # Question type: MCQ early, short_answer mid, problem late
    mastery = skill.get('mastery_level', 0.0)
    if mastery < 0.3:
        q_type = 'mcq'
    elif mastery < 0.6:
        q_type = 'short_answer'
    else:
        q_type = 'problem'

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


def _next_in_order(curriculum_nodes, current_node_id, student_skills):
    """Find the next unmastered node after current_node_id in order."""
    found_current = False
    for node in curriculum_nodes:
        if node['id'] == current_node_id:
            found_current = True
            continue
        if found_current:
            skill = student_skills.get(node['id'], {})
            if not elo.is_mastered(skill.get('mastery_level', 0.0)):
                return node['id']
    return None
