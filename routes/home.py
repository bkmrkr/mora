"""Home page — student name entry."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, session as flask_session)

from models import student as student_model
from models import session as session_model
from models.progress import get_for_student
from curriculum.skills import get_skills_for_grade, get_skill, SKILLS
from engine.elo import is_mastered

home_bp = Blueprint('home', __name__)

_LEVELS = [
    (40, 'Legend'), (35, 'Grandmaster'), (30, 'Master'), (25, 'Champion'),
    (20, 'Expert'), (15, 'Scholar'), (10, 'Learner'), (5, 'Explorer'),
    (0, 'Starter'),
]


def _level_name(mastered_count):
    for threshold, name in _LEVELS:
        if mastered_count >= threshold:
            return name
    return 'Starter'


@home_bp.route('/')
def index():
    students = student_model.get_all()
    student_info = []
    for s in students:
        progress = get_for_student(s['id'])
        progress_map = {p['skill_id']: p for p in progress}
        mastered = sum(1 for p in progress if is_mastered(p['mastery_level']))
        level = _level_name(mastered)

        # Last session info
        recent_sessions = session_model.get_for_student(s['id'], limit=1)
        last_session = None
        if recent_sessions and recent_sessions[0].get('total_questions'):
            ls = recent_sessions[0]
            q = ls['total_questions'] or 0
            c = ls['total_correct'] or 0
            last_session = {
                'accuracy': round(c / q * 100) if q > 0 else 0,
                'questions': q,
                'date': ls['started_at'][:10] if ls.get('started_at') else '',
            }

        # Focus skill: closest to mastery, unlocked
        focus = None
        best_mastery = -1
        for sid, sinfo in SKILLS.items():
            prog = progress_map.get(sid)
            m = prog['mastery_level'] if prog else 0.0
            if is_mastered(m):
                continue
            prereqs_met = all(
                is_mastered(progress_map.get(pid, {}).get('mastery_level', 0))
                for pid in sinfo.get('prerequisites', [])
            )
            if (prereqs_met or not sinfo.get('prerequisites')) and m > best_mastery:
                best_mastery = m
                focus = {'name': sinfo['name'], 'pct': round(m * 100)}

        # Practice streak
        streak_days, practiced_today = session_model.get_practice_streak(s['id'])

        student_info.append({
            'student': s,
            'mastered': mastered,
            'total_skills': 40,
            'level': level,
            'last_session': last_session,
            'focus': focus,
            'streak_days': streak_days,
            'practiced_today': practiced_today,
        })
    return render_template('home.html', student_info=student_info)


@home_bp.route('/start', methods=['POST'])
def start():
    name = request.form.get('student_name', '').strip()
    if not name:
        flash('Please enter your name.')
        return redirect(url_for('home.index'))

    student = student_model.get_by_name(name)
    if not student:
        sid = student_model.create(name)
        student = student_model.get_by_id(sid)

    # End any open sessions for this student (computes totals from attempts)
    open_sessions = session_model.get_for_student(student['id'])
    for s in open_sessions:
        if not s.get('ended_at'):
            session_model.end_session(s['id'])

    # Clear any stale session data from previous sessions
    flask_session.clear()

    # Build welcome message for returning students
    progress_rows = get_for_student(student['id'])
    if progress_rows:
        progress_by_skill = {r['skill_id']: r for r in progress_rows}
        # Find current grade (highest grade with any progress)
        grade_progress = {}
        for grade in range(1, 5):
            skills = get_skills_for_grade(grade)
            mastered = sum(
                1 for s in skills
                if is_mastered(progress_by_skill.get(s['id'], {}).get('mastery_level', 0))
            )
            grade_progress[str(grade)] = {'mastered': mastered, 'total': len(skills)}
        flask_session['welcome'] = grade_progress

        # Strength/weakness insights for welcome banner
        strength = None
        weakness = None
        practiced = [(sid, p) for sid, p in progress_by_skill.items()
                     if p.get('total_attempts', 0) >= 3]
        if practiced:
            # Strength: highest accuracy among practiced skills
            best = max(practiced, key=lambda x: x[1].get('correct_attempts', 0) / x[1]['total_attempts'])
            best_skill = get_skill(best[0])
            if best_skill:
                acc = round(best[1]['correct_attempts'] / best[1]['total_attempts'] * 100)
                if acc >= 70:
                    strength = best_skill['name']
            # Weakness: lowest accuracy among practiced, non-mastered skills
            unmastered = [(sid, p) for sid, p in practiced
                          if not is_mastered(p.get('mastery_level', 0))]
            if unmastered:
                worst = min(unmastered, key=lambda x: x[1].get('correct_attempts', 0) / x[1]['total_attempts'])
                worst_skill = get_skill(worst[0])
                if worst_skill and worst_skill['name'] != strength:
                    weakness = worst_skill['name']
        if strength or weakness:
            flask_session['welcome_insights'] = {
                'strength': strength,
                'weakness': weakness,
            }

    # Math level for session header
    total_mastered = sum(
        1 for r in progress_rows if is_mastered(r['mastery_level'])
    ) if progress_rows else 0
    flask_session['math_level'] = _level_name(total_mastered)

    # Practice streak
    streak_days, _ = session_model.get_practice_streak(student['id'])
    if streak_days >= 2:
        flask_session['practice_streak'] = streak_days

    # Set session goal (10 questions per session)
    flask_session['session_goal'] = 10
    flask_session['goal_celebrated'] = False

    session_id = session_model.create(student['id'])
    return redirect(url_for('session.question', session_id=session_id))
