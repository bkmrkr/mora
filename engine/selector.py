"""Skill selection for next question — variety-first approach.

Algorithm:
1. Find unlocked skills (prerequisites mastered or grade 1 starters)
2. Never same skill twice in a row
3. Score by need (low mastery), recency (not seen recently), virgin bonus
4. Warm-start new skills from average ELO of mastered skills
"""
import random

from engine import elo
from engine.difficulty import calibrate_from_recent
from curriculum.skills import SKILLS


def analyze_recent(recent_attempts):
    """Analyze last N attempts for per-skill stats, overall accuracy, recency.

    Args:
        recent_attempts: list of dicts with keys: skill_id, is_correct
            Ordered newest-first.

    Returns dict with overall_accuracy, per_skill stats, total_attempts, last_seen.
    """
    if not recent_attempts:
        return {
            'overall_accuracy': 0.0,
            'per_skill': {},
            'total_attempts': 0,
            'last_seen': {},
        }

    total_correct = sum(1 for a in recent_attempts if a['is_correct'])
    overall_accuracy = total_correct / len(recent_attempts)

    per_skill = {}
    for a in recent_attempts:
        sid = a['skill_id']
        if sid not in per_skill:
            per_skill[sid] = {'results': [], 'count': 0, 'correct': 0}
        is_correct = bool(a['is_correct'])
        per_skill[sid]['results'].append(is_correct)
        per_skill[sid]['count'] += 1
        if is_correct:
            per_skill[sid]['correct'] += 1

    for sid, stats in per_skill.items():
        stats['accuracy'] = stats['correct'] / stats['count'] if stats['count'] else 0

    # Recency: how many questions ago was each skill last seen?
    last_seen = {}
    for i, a in enumerate(recent_attempts):
        sid = a.get('skill_id')
        if sid and sid not in last_seen:
            last_seen[sid] = i

    return {
        'overall_accuracy': overall_accuracy,
        'per_skill': per_skill,
        'total_attempts': len(recent_attempts),
        'last_seen': last_seen,
    }


def select_skill(recent_analysis, student_progress, current_skill_id=None):
    """Pick the skill for the next question — variety-first.

    Core rule: NEVER repeat the same skill consecutively.

    Args:
        recent_analysis: output from analyze_recent()
        student_progress: dict of {skill_id: progress_row}
        current_skill_id: the skill of the question just answered

    Returns skill_id or None.
    """
    per_skill = recent_analysis.get('per_skill', {})
    last_seen = recent_analysis.get('last_seen', {})

    eligible = _get_eligible_skills(student_progress)

    if not eligible:
        # All mastered: review mode — cycle through all skills with variety
        eligible = list(SKILLS.values())

    # Hard rule: exclude current skill (never same skill twice in a row)
    candidates = [s for s in eligible if s['id'] != current_skill_id]
    if len(candidates) <= 2:
        # Too few candidates for variety — expand to all skills (mastered included)
        candidates = [s for s in SKILLS.values() if s['id'] != current_skill_id]
    if not candidates:
        candidates = eligible

    best_id, best_score = None, -1.0
    for skill in candidates:
        prog = student_progress.get(skill['id'], {})
        mastery = prog.get('mastery_level', 0.0)
        need = 1.0 - mastery

        recency = last_seen.get(skill['id'], 99)
        recency_bonus = min(recency / 3.0, 2.0)

        attempts = prog.get('total_attempts', 0)
        virgin_bonus = 0.5 if attempts == 0 else 0.0

        # Small random jitter prevents deterministic alternation on tied scores
        score = need * (0.5 + recency_bonus) + virgin_bonus + random.uniform(0, 0.05)

        if score > best_score:
            best_score = score
            best_id = skill['id']

    return best_id


def compute_question_params(skill_id, student_progress, recent_analysis):
    """Compute target difficulty and question type for a skill.

    Returns (target_difficulty, question_type).
    """
    prog = student_progress.get(skill_id, {})
    total_attempts = prog.get('total_attempts', 0)

    # Warm-start: for untouched skills, use average of proven skills
    if total_attempts == 0:
        rated = [p['skill_rating'] for p in student_progress.values()
                 if p.get('total_attempts', 0) >= 3]
        skill_rating = sum(rated) / len(rated) if rated else prog.get('skill_rating', 800.0)
    else:
        skill_rating = prog.get('skill_rating', 800.0)

    base_target = elo.target_difficulty(skill_rating)

    # Adjust based on recent performance
    skill_stats = recent_analysis.get('per_skill', {}).get(skill_id)
    if skill_stats and len(skill_stats['results']) >= 3:
        adjusted = calibrate_from_recent(base_target, skill_stats['results'])
    elif recent_analysis.get('total_attempts', 0) >= 3:
        all_results = []
        for ss in recent_analysis['per_skill'].values():
            all_results.extend(ss['results'])
        adjusted = calibrate_from_recent(base_target, all_results)
    else:
        adjusted = base_target

    # MCQ only for now — short answer disabled
    q_type = 'mcq'

    return adjusted, q_type


def _get_eligible_skills(student_progress):
    """Get unmastered skills whose prerequisites are mastered."""
    eligible = []
    for skill_id, skill in SKILLS.items():
        prog = student_progress.get(skill_id, {})
        if elo.is_mastered(prog.get('mastery_level', 0.0)):
            continue

        prereqs = skill.get('prerequisites', [])
        if prereqs:
            all_met = all(
                elo.is_mastered(
                    student_progress.get(pid, {}).get('mastery_level', 0.0)
                )
                for pid in prereqs
            )
            if not all_met:
                continue

        eligible.append(skill)
    return eligible


