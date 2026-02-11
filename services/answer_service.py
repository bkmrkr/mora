"""Process student answers: grade, update ELO, log attempt."""
import logging

from models import student_skill as skill_model
from models import attempt as attempt_model
from engine import elo
from engine.answer_matching import check_answer
from ai import answer_grader

logger = logging.getLogger(__name__)


def process_answer(student, current_question, student_answer,
                   response_time_s, session_id):
    """Grade answer, update ELO, record attempt.

    Returns dict with: is_correct, partial_score, feedback, skill_rating, mastery_level.
    """
    node_id = current_question['node_id']
    student_id = student['id']
    q_type = current_question['question_type']
    correct_answer = current_question['correct_answer']

    # Grade answer
    is_close = False
    if q_type in ('mcq', 'short_answer'):
        options = current_question.get('options') if q_type == 'mcq' else None
        is_correct, is_close = check_answer(student_answer, correct_answer, q_type, options)
        partial_score = 1.0 if is_correct else 0.0
        feedback = ''
    else:
        # Open-ended: use LLM grading
        try:
            is_correct, partial_score, feedback, _, _ = answer_grader.grade(
                current_question['content'], correct_answer, student_answer,
                current_question.get('node_name', ''),
            )
        except Exception as e:
            logger.warning('LLM grading failed: %s, falling back to exact match', e)
            is_correct, is_close = check_answer(student_answer, correct_answer)
            partial_score = 1.0 if is_correct else 0.0
            feedback = ''

    # Update ELO
    skill = skill_model.get(student_id, node_id)

    # Compute global streak for fast ramp-up (across all nodes, not just current)
    all_recent = attempt_model.get_recent(student_id, limit=30)
    streak = 0
    for a in all_recent:
        if a['is_correct']:
            streak += 1
        else:
            break

    new_rating, new_uncertainty = elo.update_skill(
        skill['skill_rating'], skill['uncertainty'],
        current_question['difficulty'], is_correct,
        streak=streak,
    )

    # Compute mastery from recent accuracy on this specific node
    recent = attempt_model.get_recent_for_node(student_id, node_id, limit=30)
    recent_results = [bool(a['is_correct']) for a in recent] + [is_correct]
    recent_accuracy = sum(recent_results) / len(recent_results)
    mastery = elo.compute_mastery(new_rating, recent_accuracy)

    # Persist skill update
    skill_model.upsert(
        student_id, node_id, new_rating, new_uncertainty, mastery,
        skill['total_attempts'] + 1,
        skill['correct_attempts'] + (1 if is_correct else 0),
    )

    # Record attempt with skill snapshots
    before_rating = skill['skill_rating']
    attempt_id = attempt_model.create(
        question_id=current_question['question_id'],
        student_id=student_id,
        session_id=session_id,
        answer_given=student_answer,
        is_correct=1 if is_correct else 0,
        partial_score=partial_score,
        response_time_seconds=response_time_s,
        curriculum_node_id=node_id,
        skill_rating_before=round(before_rating, 1),
        skill_rating_after=round(new_rating, 1),
    )

    # Record skill history for rating-over-time tracking
    skill_model.record_history(
        student_id, node_id, new_rating, new_uncertainty, mastery,
        attempt_id=attempt_id,
    )

    return {
        'is_correct': is_correct,
        'is_close': is_close,
        'partial_score': partial_score,
        'feedback': feedback,
        'correct_answer': correct_answer,
        'student_answer': student_answer,
        'question_text': current_question['content'],
        'node_name': current_question.get('node_name', ''),
        'explanation': current_question.get('explanation', ''),
        'skill_rating': round(new_rating, 1),
        'mastery_level': round(mastery, 3),
    }
