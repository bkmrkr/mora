"""Session routes — the core learning loop."""
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session as flask_session)

from models import student as student_model
from models import session as session_model
from models import attempt as attempt_model
from models import student_skill as skill_model
from models import curriculum_node as node_model
from services import question_service, answer_service
from engine import elo
from config.settings import SESSION_DEFAULTS

session_bp = Blueprint('session', __name__)


@session_bp.route('/start', methods=['POST'])
def start():
    student_id = int(request.form['student_id'])
    topic_id = int(request.form['topic_id'])
    student = student_model.get_by_id(student_id)
    if not student:
        return redirect(url_for('home.index'))

    session_id = session_model.create(student_id, topic_id)
    flask_session['topic_id'] = topic_id

    question_service.generate_next(session_id, student, topic_id)
    return redirect(url_for('session.question', session_id=session_id))


@session_bp.route('/<session_id>/question')
def question(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])
    current = flask_session.get('current_question')
    if not current:
        return redirect(url_for('session.end', session_id=session_id))

    questions_done = len(attempt_model.get_for_session(session_id))
    max_questions = SESSION_DEFAULTS['questions_per_session']

    return render_template(
        'session/question.html',
        session_id=session_id,
        student=student,
        question=current,
        questions_done=questions_done,
        max_questions=max_questions,
    )


@session_bp.route('/<session_id>/answer', methods=['POST'])
def answer(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])
    current = flask_session.get('current_question')
    if not current:
        return redirect(url_for('session.end', session_id=session_id))

    student_answer = request.form.get('answer', '').strip()
    response_time_s = float(request.form.get('response_time_s', 0))

    result = answer_service.process_answer(
        student, current, student_answer, response_time_s, session_id
    )

    if result['is_correct']:
        flask_session['last_result'] = result
        questions_done = len(attempt_model.get_for_session(session_id))
        if questions_done >= SESSION_DEFAULTS['questions_per_session']:
            return redirect(url_for('session.end', session_id=session_id))
        question_service.generate_next(session_id, student, sess['topic_id'])
        return redirect(url_for('session.question', session_id=session_id))

    flask_session['last_result'] = result
    return redirect(url_for('session.feedback', session_id=session_id))


@session_bp.route('/<session_id>/feedback')
def feedback(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])
    result = flask_session.get('last_result', {})
    current = flask_session.get('current_question', {})

    # Try to generate LLM explanation
    explanation = None
    if current:
        try:
            from ai.explainer import explain
            explanation, _, _ = explain(
                current.get('content', ''),
                current.get('correct_answer', ''),
                result.get('student_answer', ''),
                current.get('node_name', ''),
                '',
            )
        except Exception:
            explanation = {
                'explanation': f"The correct answer was: {current.get('correct_answer', '')}",
                'encouragement': 'Keep going!',
            }

    return render_template(
        'session/feedback_wrong.html',
        session_id=session_id,
        student=student,
        result=result,
        question=current,
        explanation=explanation,
    )


@session_bp.route('/<session_id>/next', methods=['POST'])
def next_question(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])

    questions_done = len(attempt_model.get_for_session(session_id))
    if questions_done >= SESSION_DEFAULTS['questions_per_session']:
        return redirect(url_for('session.end', session_id=session_id))

    question_service.generate_next(session_id, student, sess['topic_id'])
    return redirect(url_for('session.question', session_id=session_id))


@session_bp.route('/<session_id>/end')
def end(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))

    session_model.end_session(session_id)
    sess = session_model.get_by_id(session_id)
    student = student_model.get_by_id(sess['student_id'])
    attempts = attempt_model.get_for_session(session_id)

    total = sess['total_questions'] or 0
    correct = sess['total_correct'] or 0
    accuracy = round(correct / total * 100) if total > 0 else 0

    # Skills practiced
    node_ids = set(
        a['curriculum_node_id'] for a in attempts
        if a.get('curriculum_node_id')
    )
    skills_practiced = []
    for nid in node_ids:
        node = node_model.get_by_id(nid)
        sk = skill_model.get(student['id'], nid)
        if node:
            skills_practiced.append({
                'name': node['name'],
                'mastery_level': round(sk['mastery_level'], 3),
                'skill_rating': round(sk['skill_rating'], 1),
                'mastered': elo.is_mastered(sk['mastery_level']),
            })

    flask_session.pop('current_question', None)
    flask_session.pop('last_result', None)

    return render_template(
        'session/summary.html',
        session_id=session_id,
        student=student,
        session=sess,
        total=total,
        correct=correct,
        accuracy=accuracy,
        skills_practiced=skills_practiced,
    )
