"""Process student answers: grade, update ELO, log attempt."""
import logging

from models.progress import get as get_progress, upsert as upsert_progress
from models import attempt as attempt_model
from engine import elo
from engine.answer_matching import check_answer

logger = logging.getLogger(__name__)


def process_answer(student, current_question, student_answer,
                   response_time_s, session_id):
    """Grade answer, update ELO, record attempt.

    Returns dict with: is_correct, correct_answer, skill_rating, mastery_level, etc.
    """
    skill_id = current_question['skill_id']
    student_id = student['id']
    q_type = current_question['question_type']
    correct_answer = current_question['correct_answer']

    # Grade answer
    options = current_question.get('options') if q_type == 'mcq' else None
    is_correct, is_close = check_answer(student_answer, correct_answer, q_type, options)

    # Get current skill progress
    prog = get_progress(student_id, skill_id)

    # Compute streak for fast ramp-up
    all_recent = attempt_model.get_recent(student_id, limit=30)
    streak = 0
    for a in all_recent:
        if a['is_correct']:
            streak += 1
        else:
            break

    # Update ELO
    new_rating, new_uncertainty = elo.update_skill(
        prog['skill_rating'], prog['uncertainty'],
        current_question['difficulty'], is_correct,
        streak=streak,
    )

    # Compute mastery from recent accuracy on this skill
    recent = attempt_model.get_recent_for_skill(student_id, skill_id, limit=30)
    recent_results = [bool(a['is_correct']) for a in recent] + [is_correct]
    recent_accuracy = sum(recent_results) / len(recent_results)
    mastery = elo.compute_mastery(new_rating, recent_accuracy,
                                  total_attempts=prog['total_attempts'] + 1)

    # Persist
    upsert_progress(
        student_id, skill_id, new_rating, new_uncertainty, mastery,
        prog['total_attempts'] + 1,
        prog['correct_attempts'] + (1 if is_correct else 0),
    )

    before_rating = prog['skill_rating']
    attempt_model.create(
        question_id=current_question['question_id'],
        student_id=student_id,
        session_id=session_id,
        skill_id=skill_id,
        answer_given=student_answer,
        is_correct=1 if is_correct else 0,
        response_time_seconds=response_time_s,
        skill_rating_before=round(before_rating, 1),
        skill_rating_after=round(new_rating, 1),
    )

    return {
        'is_correct': is_correct,
        'is_close': is_close,
        'correct_answer': correct_answer,
        'student_answer': student_answer,
        'question_id': current_question.get('question_id'),
        'skill_id': skill_id,
        'skill_name': current_question.get('skill_name', ''),
        'explanation': current_question.get('explanation', ''),
        'skill_rating': round(new_rating, 1),
        'mastery_level': round(mastery, 3),
    }
