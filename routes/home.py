"""Home page — student name entry."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, session as flask_session)

from models import student as student_model
from models import session as session_model

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    students = student_model.get_all()
    return render_template('home.html', students=students)


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

    session_id = session_model.create(student['id'])
    return redirect(url_for('session.question', session_id=session_id))
