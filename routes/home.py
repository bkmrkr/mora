"""Home page — student and topic selection."""
from flask import Blueprint, render_template, redirect, url_for, request, flash

from models import student as student_model
from models import topic as topic_model

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    students = student_model.get_all()
    topics = topic_model.get_all()
    return render_template('home.html', students=students, topics=topics)


@home_bp.route('/onboard', methods=['POST'])
def onboard():
    """Create/retrieve student + generate curriculum for topic."""
    name = request.form.get('student_name', '').strip()
    topic = request.form.get('topic_name', '').strip()
    if not name or not topic:
        flash('Please enter both your name and a topic.')
        return redirect(url_for('home.index'))

    from services.onboarding_service import onboard as do_onboard
    try:
        student, topic_obj, nodes = do_onboard(name, topic)
    except Exception as e:
        flash(f'Error generating curriculum: {e}')
        return redirect(url_for('home.index'))

    return redirect(url_for('home.pick_topic', student_id=student['id']))


@home_bp.route('/pick-topic/<int:student_id>')
def pick_topic(student_id):
    student = student_model.get_by_id(student_id)
    if not student:
        return redirect(url_for('home.index'))
    topics = topic_model.get_all()
    return render_template('pick_topic.html', student=student, topics=topics)
