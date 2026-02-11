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

session_bp = Blueprint('session', __name__)


def _compute_topic_mastery(student_id, topic_id):
    """Average mastery_level across all curriculum nodes for a topic, as 0-100."""
    nodes = node_model.get_for_topic(topic_id)
    if not nodes:
        return 0
    total = sum(skill_model.get(student_id, n['id'])['mastery_level'] for n in nodes)
    return round(total / len(nodes) * 100)


def _get_topic_progress(student_id, topic_id):
    """Per-node mastery data for the right panel progress display."""
    nodes = node_model.get_for_topic(topic_id)
    progress = []
    for node in nodes:
        sk = skill_model.get(student_id, node['id'])
        progress.append({
            'name': node['name'],
            'mastery_pct': round(sk['mastery_level'] * 100),
            'skill_rating': round(sk['skill_rating'], 1),
            'total_attempts': sk['total_attempts'],
            'mastered': elo.is_mastered(sk['mastery_level']),
        })
    return progress


def _get_session_stats(session_id):
    """Compute running session stats from attempts."""
    attempts = attempt_model.get_for_session(session_id)
    total = len(attempts)
    correct = sum(1 for a in attempts if a['is_correct'])
    accuracy = round(correct / total * 100) if total > 0 else 0
    return {'total': total, 'correct': correct, 'accuracy': accuracy}


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
        # Always retry — sessions never auto-end
        question_service.generate_next(session_id, student, sess['topic_id'])
        current = flask_session.get('current_question')
    if not current:
        # Generation failed twice — show retry page, not end
        topic_mastery = _compute_topic_mastery(student['id'], sess['topic_id'])
        topic_progress = _get_topic_progress(student['id'], sess['topic_id'])
        session_stats = _get_session_stats(session_id)
        return render_template(
            'session/retry.html',
            session_id=session_id, student=student,
            topic_mastery=topic_mastery, topic_progress=topic_progress,
            session_stats=session_stats,
        )

    topic_mastery = _compute_topic_mastery(student['id'], sess['topic_id'])
    last_result = flask_session.get('last_result')
    topic_progress = _get_topic_progress(student['id'], sess['topic_id'])
    session_stats = _get_session_stats(session_id)

    return render_template(
        'session/question.html',
        session_id=session_id,
        student=student,
        question=current,
        topic_mastery=topic_mastery,
        last_result=last_result,
        topic_progress=topic_progress,
        session_stats=session_stats,
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

    # Capture before-state for delta display
    node_id = current['node_id']
    before_skill = skill_model.get(student['id'], node_id)
    before_rating = round(before_skill['skill_rating'], 1)
    before_mastery = _compute_topic_mastery(student['id'], sess['topic_id'])

    result = answer_service.process_answer(
        student, current, student_answer, response_time_s, session_id
    )

    # Compute deltas
    after_mastery = _compute_topic_mastery(student['id'], sess['topic_id'])
    rating_delta = round(result['skill_rating'] - before_rating, 1)
    mastery_delta = after_mastery - before_mastery
    result['rating_delta'] = rating_delta
    result['mastery_before'] = before_mastery
    result['mastery_after'] = after_mastery
    result['mastery_delta'] = mastery_delta

    if result['is_correct']:
        flask_session['last_result'] = result
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

    topic_mastery = _compute_topic_mastery(student['id'], sess['topic_id'])

    return render_template(
        'session/feedback_wrong.html',
        session_id=session_id,
        student=student,
        result=result,
        question=current,
        explanation=explanation,
        topic_mastery=topic_mastery,
    )


@session_bp.route('/<session_id>/next', methods=['POST'])
def next_question(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])

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
