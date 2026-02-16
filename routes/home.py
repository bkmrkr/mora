"""Home page — student name entry."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, session as flask_session)

from models import student as student_model
from models import session as session_model
from models.progress import get_for_student
from curriculum.skills import get_skills_for_grade
from engine.elo import is_mastered

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    students = student_model.get_all()
    student_info = []
    for s in students:
        progress = get_for_student(s['id'])
        mastered = sum(1 for p in progress if is_mastered(p['mastery_level']))
        student_info.append({'student': s, 'mastered': mastered})
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

    session_id = session_model.create(student['id'])
    return redirect(url_for('session.question', session_id=session_id))
