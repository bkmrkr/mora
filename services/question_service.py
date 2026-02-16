"""Question generation: select skill → pick template → generate → store."""
import json
import logging
import random
from datetime import datetime, date

from models import attempt as attempt_model
from models import question as question_model
from models import session as session_model
from models.progress import get as get_progress, get_for_student
from engine.selector import analyze_recent, select_skill, compute_question_params
from engine import elo
from curriculum.skills import get_skill, SKILLS
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
    is_retry = False
    if retry_skill_id and retry_skill_id in TEMPLATES:
        skill_id = retry_skill_id
        is_retry = True
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

    # Review reason: explain why this mastered skill is being revisited
    review_reason = None
    if is_review and prog.get('last_updated'):
        try:
            last_date = datetime.fromisoformat(prog['last_updated']).date()
            days_ago = (date.today() - last_date).days
            if days_ago >= 7:
                review_reason = f"Haven't practiced in {days_ago} days"
            elif days_ago >= 2:
                review_reason = f'Last practiced {days_ago} days ago'
            else:
                review_reason = 'Keeping sharp'
        except (ValueError, TypeError):
            review_reason = 'Keeping sharp'
    elif is_review:
        review_reason = 'Quick refresh'

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

    # Show skill tip when student is struggling (last 2+ wrong on this skill)
    skill_tip = None
    if not is_review and len(skill_attempts) >= 2:
        recent_wrong = 0
        for a in skill_attempts:
            if not a['is_correct']:
                recent_wrong += 1
            else:
                break  # stop at first correct (consecutive wrong streak from top)
        if recent_wrong >= 2:
            skill_tip = skill.get('tip')

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
        'review_reason': review_reason,
        'skill_tip': skill_tip,
    }
    # "Why this question?" — metacognition helper (review reasons shown in badge)
    if is_retry:
        why_reason = "Let's try this skill again after the miss."
    elif is_review:
        why_reason = None  # review_reason already shown in badge
    elif prog['total_attempts'] == 0:
        why_reason = 'New skill! Your prerequisites are all mastered.'
    elif len(skill_attempts) >= 4:
        recent_correct = sum(1 for a in skill_attempts[:4] if a['is_correct'])
        if recent_correct <= 2:
            why_reason = f'You got {recent_correct} of the last 4 right — needs practice.'
        elif mastery_pct >= 50:
            why_reason = f'{mastery_pct}% mastered — getting close!'
        else:
            why_reason = 'Building up this skill step by step.'
    elif mastery_pct >= 50:
        why_reason = f'{mastery_pct}% mastered — almost there!'
    else:
        why_reason = None
    question_dict['why_reason'] = why_reason

    # Story theme for word problems — visual variety
    story_theme = None
    if 'word' in skill_id:
        content_lower = q_data['question'].lower()
        themes = [
            ('apple', '🍎', 'apple'), ('cookie', '🍪', 'cookie'),
            ('bird', '🐦', 'bird'), ('sticker', '⭐', 'sticker'),
            ('marble', '🔮', 'marble'), ('book', '📚', 'book'),
            ('ticket', '🎟', 'ticket'), ('flower', '🌸', 'flower'),
            ('coin', '🪙', 'coin'), ('toy', '🧸', 'toy'),
            ('pie', '🥧', 'pie'), ('pizza', '🍕', 'pizza'),
            ('pencil', '✏️', 'pencil'), ('car', '🚗', 'car'),
            ('fish', '🐟', 'fish'), ('star', '⭐', 'star'),
        ]
        for keyword, emoji, theme_name in themes:
            if keyword in content_lower:
                story_theme = {'emoji': emoji, 'name': theme_name}
                break
    question_dict['story_theme'] = story_theme

    # Unlock preview: what does mastering this skill unlock?
    unlock_preview = None
    if not is_review and mastery_pct < 65:
        for sid, sinfo in SKILLS.items():
            if skill_id in sinfo.get('prerequisites', []):
                # Check if this downstream skill is still locked
                s_prog = student_progress.get(sid, {})
                if not elo.is_mastered(s_prog.get('mastery_level', 0.0)):
                    unlock_preview = sinfo['name']
                    break
    question_dict['unlock_preview'] = unlock_preview

    # Clock params for SVG generation at render time (avoids cookie bloat)
    if 'clock_hour' in q_data:
        question_dict['clock_hour'] = q_data['clock_hour']
        question_dict['clock_minute'] = q_data['clock_minute']

    session_model.update_current_question(session_id, question_id)
    return question_dict
