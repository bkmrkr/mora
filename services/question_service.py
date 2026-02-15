"""Question generation: select skill → pick template → generate → store."""
import json
import logging
import random

from models import attempt as attempt_model
from models import question as question_model
from models import session as session_model
from models.progress import get as get_progress, get_for_student
from engine import elo
from engine.selector import analyze_recent, select_skill, compute_question_params
from curriculum.skills import SKILLS, get_skill
from curriculum.templates.grade1 import GRADE1_TEMPLATES

logger = logging.getLogger(__name__)

# Registry of all template functions by skill_id
TEMPLATES = {}
TEMPLATES.update(GRADE1_TEMPLATES)
# Grades 2-4 will be added here in Phase 6


def generate_next(session_id, student, current_skill_id=None):
    """Select skill, generate question from template, store in DB.

    Returns question_dict or None.
    """
    student_id = student['id']

    # Build progress dict
    progress_rows = get_for_student(student_id)
    student_progress = {r['skill_id']: r for r in progress_rows}

    # Recent attempts for analysis
    recent_attempts = attempt_model.get_recent(student_id, limit=30)
    analysis = analyze_recent(recent_attempts)

    # Select skill
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

    # Store in DB
    question_id = question_model.create(
        skill_id=q_data['skill_id'],
        content=q_data['question'],
        question_type=q_type,
        options=json.dumps(q_data['options']) if q_data.get('options') else None,
        correct_answer=q_data['correct_answer'],
        explanation=q_data.get('explanation', ''),
        difficulty=target_diff,
        template_id=q_data.get('template_id'),
    )

    question_dict = {
        'question_id': question_id,
        'skill_id': skill_id,
        'skill_name': skill['name'],
        'content': q_data['question'],
        'question_type': q_type,
        'options': q_data.get('options'),
        'correct_answer': q_data['correct_answer'],
        'explanation': q_data.get('explanation', ''),
        'difficulty': target_diff,
    }

    session_model.update_current_question(session_id, question_id)
    return question_dict
