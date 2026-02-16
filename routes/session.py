"""Session routes — the core learning loop."""
import json
import logging

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session as flask_session)

from models import student as student_model
from models import session as session_model
from models import attempt as attempt_model
from models.progress import get as get_progress, get_for_student
from services import question_service, answer_service
from curriculum.skills import get_skill, SKILLS
from curriculum.templates.common import generate_clock_svg
from engine import elo

logger = logging.getLogger(__name__)
session_bp = Blueprint('session', __name__)


def _get_session_stats(session_id):
    attempts = attempt_model.get_for_session(session_id)
    total = len(attempts)
    correct = sum(1 for a in attempts if a['is_correct'])
    accuracy = round(correct / total * 100) if total > 0 else 0
    return {'total': total, 'correct': correct, 'accuracy': accuracy}


@session_bp.route('/<session_id>/question')
def question(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    if sess.get('ended_at'):
        return redirect(url_for('session.end', session_id=session_id))
    student = student_model.get_by_id(sess['student_id'])

    current = flask_session.get('current_question')
    # Validate required v2 fields — discard stale/corrupt session data
    required_keys = {'skill_id', 'question_id', 'correct_answer', 'options', 'question_type'}
    if current and not required_keys.issubset(current.keys()):
        logger.warning('Discarding invalid current_question: missing %s',
                       required_keys - set(current.keys()))
        flask_session.pop('current_question', None)
        current = None
    if not current:
        current_skill = flask_session.get('last_skill_id')
        current = question_service.generate_next(session_id, student, current_skill)
        if current:
            flask_session['current_question'] = current

    if not current:
        return render_template('session/retry.html',
                               session_id=session_id, student=student)

    last_result = flask_session.get('last_result')
    session_stats = _get_session_stats(session_id)
    streak = flask_session.get('streak', 0)

    # Welcome message and practice streak (shown once on first question)
    welcome = flask_session.pop('welcome', None)
    practice_streak = flask_session.pop('practice_streak', None)

    # Session goal tracking
    session_goal = flask_session.get('session_goal', 10)
    goal_reached = session_stats['total'] >= session_goal
    goal_celebrated = flask_session.get('goal_celebrated', False)
    # Mark celebrated so we only show the celebration once
    if goal_reached and not goal_celebrated:
        flask_session['goal_celebrated'] = True
        show_goal_celebration = True
    else:
        show_goal_celebration = False

    # Generate clock SVG at render time (not stored in cookie)
    visual_svg = None
    if 'clock_hour' in current:
        visual_svg = generate_clock_svg(current['clock_hour'], current['clock_minute'])

    return render_template(
        'session/question.html',
        session_id=session_id,
        student=student,
        question=current,
        last_result=last_result,
        session_stats=session_stats,
        visual_svg=visual_svg,
        streak=streak,
        welcome=welcome,
        session_goal=session_goal,
        goal_reached=goal_reached,
        show_goal_celebration=show_goal_celebration,
        practice_streak=practice_streak,
    )


@session_bp.route('/<session_id>/answer', methods=['POST'])
def answer(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    if sess.get('ended_at'):
        return redirect(url_for('session.end', session_id=session_id))
    student = student_model.get_by_id(sess['student_id'])
    current = flask_session.get('current_question')
    if not current or not {'skill_id', 'question_id', 'correct_answer', 'question_type'}.issubset(current.keys()):
        flask_session.pop('current_question', None)
        return redirect(url_for('session.question', session_id=session_id))

    submitted_qid = request.form.get('question_id', type=int)
    if submitted_qid and submitted_qid != current.get('question_id'):
        return redirect(url_for('session.question', session_id=session_id))

    student_answer = request.form.get('answer', '').strip()
    try:
        response_time_s = float(request.form.get('response_time_s', 0))
    except (ValueError, TypeError):
        response_time_s = 0.0

    if not student_answer:
        return redirect(url_for('session.question', session_id=session_id))

    result = answer_service.process_answer(
        student, current, student_answer, response_time_s, session_id
    )

    flask_session['last_result'] = result
    flask_session['last_skill_id'] = current['skill_id']
    session_model.update_last_result(session_id, json.dumps(result))

    # Track streak
    streak = flask_session.get('streak', 0)
    if result['is_correct']:
        streak += 1
        flask_session['streak'] = streak
        result['streak'] = streak
        flask_session['last_result'] = result  # update with streak
    else:
        flask_session['best_streak'] = max(flask_session.get('best_streak', 0), streak)
        result['broken_streak'] = streak  # how many they had before missing
        flask_session['last_result'] = result
        flask_session['streak'] = 0

    flask_session.pop('current_question', None)
    session_model.update_current_question(session_id, None)

    if result['is_correct']:
        # Generate next question immediately
        next_q = question_service.generate_next(
            session_id, student, current['skill_id']
        )
        if next_q:
            flask_session['current_question'] = next_q
        return redirect(url_for('session.question', session_id=session_id))
    return redirect(url_for('session.feedback', session_id=session_id))


@session_bp.route('/<session_id>/feedback')
def feedback(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    if sess.get('ended_at'):
        return redirect(url_for('session.end', session_id=session_id))
    student = student_model.get_by_id(sess['student_id'])
    result = flask_session.get('last_result')
    if not result and sess.get('last_result_json'):
        result = json.loads(sess['last_result_json'])
        flask_session['last_result'] = result
    result = result or {}

    return render_template(
        'session/feedback_wrong.html',
        session_id=session_id,
        student=student,
        result=result,
    )


@session_bp.route('/<session_id>/next', methods=['POST'])
def next_question(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    if sess.get('ended_at'):
        return redirect(url_for('session.end', session_id=session_id))
    student = student_model.get_by_id(sess['student_id'])

    if not flask_session.get('current_question'):
        last_skill = flask_session.get('last_skill_id')
        next_q = question_service.generate_next(session_id, student, last_skill)
        if next_q:
            flask_session['current_question'] = next_q
    return redirect(url_for('session.question', session_id=session_id))


@session_bp.route('/<session_id>/end')
def end(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))

    if not sess.get('ended_at'):
        session_model.end_session(session_id)
        sess = session_model.get_by_id(session_id)
    student = student_model.get_by_id(sess['student_id'])
    attempts = attempt_model.get_for_session(session_id)

    total = sess['total_questions'] or 0
    correct = sess['total_correct'] or 0
    accuracy = round(correct / total * 100) if total > 0 else 0

    # Per-skill session accuracy
    skill_attempts = {}
    for a in attempts:
        sid = a.get('skill_id')
        if not sid:
            continue
        if sid not in skill_attempts:
            skill_attempts[sid] = {'correct': 0, 'total': 0}
        skill_attempts[sid]['total'] += 1
        if a['is_correct']:
            skill_attempts[sid]['correct'] += 1

    skills_practiced = []
    for sid, counts in skill_attempts.items():
        skill = get_skill(sid)
        prog = get_progress(student['id'], sid)
        if skill:
            session_acc = round(counts['correct'] / counts['total'] * 100) if counts['total'] > 0 else 0
            skills_practiced.append({
                'name': skill['name'],
                'mastery_pct': round(prog['mastery_level'] * 100),
                'skill_rating': round(prog['skill_rating'], 1),
                'mastered': elo.is_mastered(prog['mastery_level']),
                'session_correct': counts['correct'],
                'session_total': counts['total'],
                'session_accuracy': session_acc,
            })

    # Average response time
    times = [a['response_time_seconds'] for a in attempts
             if a.get('response_time_seconds') and a['response_time_seconds'] > 0]
    avg_time = round(sum(times) / len(times), 1) if times else None

    best_streak = max(
        flask_session.get('best_streak', 0),
        flask_session.get('streak', 0),
    )

    # Find focus skill: unmastered skill closest to mastery threshold
    focus_skill = None
    all_progress = get_for_student(student['id'])
    progress_map = {p['skill_id']: p for p in all_progress}
    best_mastery = -1
    for sid, sinfo in SKILLS.items():
        prog = progress_map.get(sid)
        mastery = prog['mastery_level'] if prog else 0.0
        if not elo.is_mastered(mastery) and mastery > best_mastery:
            # Check prerequisites are met
            prereqs_met = all(
                elo.is_mastered(progress_map.get(pid, {}).get('mastery_level', 0))
                for pid in sinfo.get('prerequisites', [])
            )
            if prereqs_met or not sinfo.get('prerequisites'):
                best_mastery = mastery
                focus_skill = {
                    'name': sinfo['name'],
                    'grade': sinfo['grade'],
                    'mastery_pct': round(mastery * 100),
                }

    # Answer timeline (ordered dots for correct/wrong)
    answer_timeline = [bool(a['is_correct']) for a in attempts]

    # Practice streak
    practice_streak, _ = session_model.get_practice_streak(student['id'])

    # Personalized summary message
    if accuracy >= 90:
        summary_headline = 'Outstanding!'
        summary_message = f'You nailed it, {student["name"]}!'
    elif accuracy >= 70:
        summary_headline = 'Great Session!'
        summary_message = f'Solid work, {student["name"]}!'
    elif accuracy >= 50:
        summary_headline = 'Good Effort!'
        summary_message = f'Keep it up, {student["name"]}!'
    else:
        summary_headline = 'Session Complete!'
        summary_message = f'Every practice session makes you stronger, {student["name"]}!'

    # Session insight — find the best and worst skill this session
    session_insight = None
    if skills_practiced:
        best = max(skills_practiced, key=lambda s: s['session_accuracy'])
        worst = min(skills_practiced, key=lambda s: s['session_accuracy'])
        if best['session_accuracy'] == 100 and len(skills_practiced) > 1:
            session_insight = f'Perfect on {best["name"]}!'
        elif worst['session_accuracy'] < 50 and len(skills_practiced) > 1:
            session_insight = f'{worst["name"]} needs more practice — you\'ll get there!'
        elif any(s['mastered'] for s in skills_practiced):
            mastered_names = [s['name'] for s in skills_practiced if s['mastered']]
            session_insight = f'{mastered_names[0]} is mastered!'

    flask_session.pop('current_question', None)
    flask_session.pop('last_result', None)
    flask_session.pop('last_skill_id', None)
    flask_session.pop('streak', None)
    flask_session.pop('best_streak', None)

    return render_template(
        'session/summary.html',
        session_id=session_id,
        student=student,
        total=total,
        correct=correct,
        accuracy=accuracy,
        skills_practiced=skills_practiced,
        best_streak=best_streak,
        avg_time=avg_time,
        focus_skill=focus_skill,
        answer_timeline=answer_timeline,
        practice_streak=practice_streak,
        summary_headline=summary_headline,
        summary_message=summary_message,
        session_insight=session_insight,
    )
