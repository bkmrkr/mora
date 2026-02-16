"""Process student answers: grade, update ELO, log attempt."""
import logging

from models.progress import get as get_progress, upsert as upsert_progress
from models import attempt as attempt_model
from engine import elo
from engine.answer_matching import check_answer
from curriculum.skills import get_skill, get_skills_for_grade, SKILLS

logger = logging.getLogger(__name__)


def _parse_number(s):
    """Try to parse a string as a number (int or float)."""
    s = s.strip()
    try:
        if '/' in s:
            parts = s.split('/')
            return float(parts[0]) / float(parts[1])
        if '.' in s:
            return float(s)
        return int(s)
    except (ValueError, ZeroDivisionError):
        return None


def _analyze_mistake(student_answer, correct_answer, skill_id):
    """Detect common mistake patterns and return a helpful hint."""
    sa = _parse_number(student_answer)
    ca = _parse_number(correct_answer)

    if sa is None or ca is None:
        return ''

    diff = sa - ca

    # Off-by-one (most common for counting/addition/subtraction)
    if abs(diff) == 1:
        return 'You were off by 1 — try counting again carefully.'

    # Off by 10 (place value error)
    if abs(diff) == 10:
        return 'Off by 10 — check your tens place.'

    # Off by 100
    if abs(diff) == 100:
        return 'Off by 100 — check your hundreds place.'

    # Swapped digits (e.g., answered 21 instead of 12)
    cs = correct_answer.strip()
    ss = student_answer.strip()
    if len(cs) == 2 and len(ss) == 2 and cs[0] == ss[1] and cs[1] == ss[0]:
        return 'Looks like the digits got swapped — check tens and ones.'

    # Wrong operation (e.g., added instead of subtracted, or vice versa)
    if ca != 0 and sa != 0:
        if abs(diff) == 2 * min(abs(sa), abs(ca)):
            return 'Double-check which operation the problem is asking for.'

    # Multiplication vs addition confusion (common in grade 2-3)
    if 'mult' in skill_id or 'div' in skill_id:
        if abs(diff) > 0:
            return 'Remember: multiplication means equal groups, not adding.'

    return ''


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

    # Detect mastery milestone
    was_mastered = elo.is_mastered(prog['mastery_level'])
    now_mastered = elo.is_mastered(mastery)
    just_mastered = now_mastered and not was_mastered

    # Check grade completion and newly unlocked skills
    grade_completed = None
    unlocked_skills = []
    if just_mastered:
        skill_info = get_skill(skill_id)
        if skill_info:
            grade = skill_info['grade']
            grade_skills = get_skills_for_grade(grade)
            all_mastered = all(
                elo.is_mastered(get_progress(student_id, s['id'])['mastery_level'])
                for s in grade_skills
            )
            if all_mastered:
                grade_completed = grade

        # Find skills that have this skill as a prerequisite
        for sid, s in SKILLS.items():
            if skill_id not in s.get('prerequisites', []):
                continue
            # Check if ALL prerequisites are now met
            all_prereqs_met = all(
                elo.is_mastered(get_progress(student_id, pid)['mastery_level'])
                for pid in s['prerequisites']
            )
            if all_prereqs_met:
                # Only include if not already mastered
                if not elo.is_mastered(get_progress(student_id, sid)['mastery_level']):
                    unlocked_skills.append({
                        'name': s['name'],
                        'grade': s['grade'],
                    })

    # Speed feedback for correct answers
    speed_label = None
    if is_correct and response_time_s > 0:
        if response_time_s <= 3:
            speed_label = 'Lightning!'
        elif response_time_s <= 6:
            speed_label = 'Quick!'

    rating_change = round(new_rating - before_rating, 1)

    skill_info = get_skill(skill_id)
    skill_tip = skill_info.get('tip', '') if skill_info else ''

    # Mistake analysis: identify what the student likely confused
    mistake_hint = ''
    if not is_correct:
        mistake_hint = _analyze_mistake(student_answer, correct_answer, skill_id)

    # Personalized encouragement message (correct answers)
    personal_message = ''
    if is_correct:
        skill_name = current_question.get('skill_name', '')
        skill_total = prog['total_attempts']  # before this attempt
        skill_correct = prog['correct_attempts']

        if skill_total == 0:
            # First time seeing this skill
            personal_message = f'Great start with {skill_name}!'
        elif just_mastered:
            personal_message = f'You mastered {skill_name}!'
        else:
            # Check for revenge correct (previous attempt on this skill was wrong)
            # limit=2 because current attempt is already persisted at [0]
            skill_recent = attempt_model.get_recent_for_skill(student_id, skill_id, limit=2)
            was_last_wrong = len(skill_recent) >= 2 and not skill_recent[1]['is_correct']

            if was_last_wrong:
                personal_message = f'You got {skill_name} this time!'
            elif current_question['difficulty'] - before_rating > 100:
                personal_message = 'That was a tough one — well done!'
            elif mastery >= 0.55 and not now_mastered:
                personal_message = f'{skill_name} is almost mastered — keep going!'

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
        'rating_change': rating_change,
        'mastery_level': round(mastery, 3),
        'just_mastered': just_mastered,
        'grade_completed': grade_completed,
        'unlocked_skills': unlocked_skills,
        'speed_label': speed_label,
        'response_time_s': round(response_time_s, 1),
        'skill_tip': skill_tip,
        'mistake_hint': mistake_hint,
        'personal_message': personal_message,
    }
