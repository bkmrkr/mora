"""Session routes — the core learning loop."""
import json
import logging

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session as flask_session, jsonify)

from models import student as student_model
from models import session as session_model
from models import attempt as attempt_model
from models import student_skill as skill_model
from models import curriculum_node as node_model
from models import question as question_model
from services import question_service, answer_service
from engine import elo

logger = logging.getLogger(__name__)
session_bp = Blueprint('session', __name__)


def _load_question_from_db(question_id):
    """Reconstruct a question_dict from the DB (for session resume after restart)."""
    q = question_model.get_by_id(question_id)
    if not q:
        return None
    node = node_model.get_by_id(q['curriculum_node_id'])
    difficulty = q['difficulty'] or 0
    norm_diff = max(0.0, min(1.0, (difficulty - 500) / 600))
    difficulty_score = round(norm_diff * 9) + 1
    p_correct = q['estimated_p_correct'] or 0
    options = json.loads(q['options']) if q['options'] else None
    return {
        'question_id': q['id'],
        'node_id': q['curriculum_node_id'],
        'node_name': node['name'] if node else '',
        'content': q['content'],
        'question_type': q['question_type'],
        'options': options,
        'correct_answer': q['correct_answer'],
        'explanation': q.get('explanation', ''),
        'difficulty': difficulty,
        'difficulty_score': difficulty_score,
        'p_correct': round(p_correct * 100) if p_correct else 0,
    }


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
    if not current and sess.get('current_question_id'):
        # Resume from DB after restart
        current = _load_question_from_db(sess['current_question_id'])
        if current:
            flask_session['current_question'] = current
            logger.info('Resumed question %d from DB for session %s',
                        sess['current_question_id'], session_id)
    if not current:
        # Generate fresh
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
    if not current and sess.get('current_question_id'):
        current = _load_question_from_db(sess['current_question_id'])
    if not current:
        return redirect(url_for('session.end', session_id=session_id))

    # Guard: reject stale form submissions (double-click / browser retry).
    # The form includes question_id — if it doesn't match current_question,
    # this is a stale POST from a previous page load.
    submitted_qid = request.form.get('question_id', type=int)
    if submitted_qid and submitted_qid != current.get('question_id'):
        logger.warning(
            'Stale answer submission: form question_id=%d, current=%d — ignoring',
            submitted_qid, current.get('question_id', -1),
        )
        return redirect(url_for('session.question', session_id=session_id))

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

    flask_session['last_result'] = result
    session_model.update_last_result(session_id, json.dumps(result))

    # Clear the answered question — it must never be served again.
    # Without this, wrong-path with no cache would re-serve the same question.
    flask_session.pop('current_question', None)
    session_model.update_current_question(session_id, None)

    # Try pre-cached question for the actual outcome
    cached = question_service.pop_cached(
        student['id'], session_id, is_correct=result['is_correct'],
    )
    if cached:
        flask_session['current_question'] = cached
        session_model.update_current_question(session_id, cached['question_id'])
    elif result['is_correct']:
        question_service.generate_next(session_id, student, sess['topic_id'],
                                       last_was_correct=True)

    if result['is_correct']:
        return redirect(url_for('session.question', session_id=session_id))
    return redirect(url_for('session.feedback', session_id=session_id))


@session_bp.route('/<session_id>/feedback')
def feedback(session_id):
    sess = session_model.get_by_id(session_id)
    if not sess:
        return redirect(url_for('home.index'))
    student = student_model.get_by_id(sess['student_id'])
    result = flask_session.get('last_result')
    if not result and sess.get('last_result_json'):
        result = json.loads(sess['last_result_json'])
        flask_session['last_result'] = result
    result = result or {}
    current = flask_session.get('current_question')
    if not current and sess.get('current_question_id'):
        current = _load_question_from_db(sess['current_question_id'])
    current = current or {}

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

    # Wrong-path question may already be set by answer() from dual cache.
    # If not, generate fresh (after wrong answer).
    current = flask_session.get('current_question')
    if not current:
        question_service.generate_next(session_id, student, sess['topic_id'],
                                       last_was_correct=False)
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


@session_bp.route('/<session_id>/precache', methods=['POST'])
def precache(session_id):
    """Pre-generate two questions (correct/wrong paths) while student thinks."""
    sess = session_model.get_by_id(session_id)
    if not sess:
        return '', 204
    student = student_model.get_by_id(sess['student_id'])
    if not student:
        return '', 204
    current_question = flask_session.get('current_question')
    if not current_question and sess.get('current_question_id'):
        current_question = _load_question_from_db(sess['current_question_id'])
    if not current_question:
        return '', 204
    try:
        question_service.precache_next(
            session_id, student, sess['topic_id'],
            current_question=current_question,
        )
    except Exception as e:
        logger.warning('Precache failed for session %s: %s', session_id, e)
    return '', 204
