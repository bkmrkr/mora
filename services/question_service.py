"""Question generation: select skill → pick template → generate → store."""
import json
import logging
import random

from models import attempt as attempt_model
from models import question as question_model
from models import session as session_model
from models.progress import get as get_progress, get_for_student
from engine.selector import analyze_recent, select_skill, compute_question_params
from engine import elo
from curriculum.skills import get_skill
from curriculum.templates.grade1 import GRADE1_TEMPLATES
from curriculum.templates.grade2 import GRADE2_TEMPLATES
from curriculum.templates.grade3 import GRADE3_TEMPLATES
from curriculum.templates.grade4 import GRADE4_TEMPLATES

logger = logging.getLogger(__name__)

# Registry of all template functions by skill_id
TEMPLATES = {}
TEMPLATES.update(GRADE1_TEMPLATES)
TEMPLATES.update(GRADE2_TEMPLATES)
TEMPLATES.update(GRADE3_TEMPLATES)
TEMPLATES.update(GRADE4_TEMPLATES)


def generate_next(session_id, student, current_skill_id=None, retry_skill_id=None):
    """Select skill, generate question from template, store in DB.

    Args:
        retry_skill_id: if set, force this skill (for immediate retry after wrong).

    Returns question_dict or None.
    """
    student_id = student['id']

    # Build progress dict
    progress_rows = get_for_student(student_id)
    student_progress = {r['skill_id']: r for r in progress_rows}

    # Recent attempts for analysis
    recent_attempts = attempt_model.get_recent(student_id, limit=30)
    analysis = analyze_recent(recent_attempts)

    # Select skill (retry overrides normal selection)
    if retry_skill_id and retry_skill_id in TEMPLATES:
        skill_id = retry_skill_id
    else:
        skill_id = select_skill(analysis, student_progress, current_skill_id)
    if not skill_id:
        return None

    skill = get_skill(skill_id)
    if not skill:
        return None

    # Compute difficulty and question type
    prog = get_progress(student_id, skill_id)
    student_progress[skill_id] = prog  # ensure it's in the dict
    target_diff, q_type = compute_question_params(skill_id, student_progress, analysis)

    # Pick template and generate
    templates = TEMPLATES.get(skill_id, [])
    if not templates:
        logger.warning('No templates for skill %s', skill_id)
        return None

    template_fn = random.choice(templates)
    q_data = template_fn(target_diff)

    # Use intrinsic difficulty from template if available, else fall back to target
    question_difficulty = q_data.get('difficulty', target_diff)

    # Store in DB
    question_id = question_model.create(
        skill_id=q_data['skill_id'],
        content=q_data['question'],
        question_type=q_type,
        options=json.dumps(q_data['options']) if q_data.get('options') else None,
        correct_answer=q_data['correct_answer'],
        explanation=q_data.get('explanation', ''),
        difficulty=question_difficulty,
        template_id=q_data.get('template_id'),
    )

    mastery_pct = round(prog['mastery_level'] * 100)

    # Detect review mode: skill is already mastered
    is_review = elo.is_mastered(prog['mastery_level'])

    # Difficulty label based on gap between question and student
    if is_review:
        difficulty_label = 'Review'
    else:
        gap = question_difficulty - prog['skill_rating']
        if gap < -150:
            difficulty_label = 'Warm-up'
        elif gap < 50:
            difficulty_label = 'On track'
        elif gap < 200:
            difficulty_label = 'Stretch'
        else:
            difficulty_label = 'Challenge'

    # Compute skill momentum from recent attempts
    skill_attempts = attempt_model.get_recent_for_skill(student_id, skill_id, limit=6)
    if len(skill_attempts) >= 4:
        # Compare recent half vs older half accuracy
        mid = len(skill_attempts) // 2
        recent_half = skill_attempts[:mid]  # newest first
        older_half = skill_attempts[mid:]
        recent_acc = sum(1 for a in recent_half if a['is_correct']) / len(recent_half)
        older_acc = sum(1 for a in older_half if a['is_correct']) / len(older_half)
        diff = recent_acc - older_acc
        if diff > 0.15:
            momentum = 'rising'
        elif diff < -0.15:
            momentum = 'falling'
        else:
            momentum = 'steady'
    else:
        momentum = None  # not enough data

    question_dict = {
        'question_id': question_id,
        'skill_id': skill_id,
        'skill_name': skill['name'],
        'skill_grade': skill['grade'],
        'mastery_pct': mastery_pct,
        'difficulty_label': difficulty_label,
        'momentum': momentum,
        'content': q_data['question'],
        'question_type': q_type,
        'options': q_data.get('options'),
        'correct_answer': q_data['correct_answer'],
        'explanation': q_data.get('explanation', ''),
        'difficulty': question_difficulty,
        'is_review': is_review,
    }
    # Clock params for SVG generation at render time (avoids cookie bloat)
    if 'clock_hour' in q_data:
        question_dict['clock_hour'] = q_data['clock_hour']
        question_dict['clock_minute'] = q_data['clock_minute']

    session_model.update_current_question(session_id, question_id)
    return question_dict
