"""Admin routes for question testing and review."""
import json
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db.database import query_db, execute_db
from models.question import get_by_id
from models.curriculum_node import get_by_id as get_node_by_id
from models.topic import get_by_id as get_topic_by_id

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def get_pending_questions(limit=20):
    """Get questions pending review."""
    return query_db("""
        SELECT q.*, cn.name as node_name, t.name as topic_name
        FROM questions q
        JOIN curriculum_nodes cn ON q.curriculum_node_id = cn.id
        JOIN topics t ON cn.topic_id = t.id
        WHERE q.test_status = 'pending_review'
        ORDER BY q.created_at DESC
        LIMIT ?
    """, (limit,))


def get_rejected_questions(limit=20):
    """Get rejected questions for analysis."""
    return query_db("""
        SELECT q.*, cn.name as node_name, t.name as topic_name
        FROM questions q
        JOIN curriculum_nodes cn ON q.curriculum_node_id = cn.id
        JOIN topics t ON cn.topic_id = t.id
        WHERE q.test_status = 'rejected'
        ORDER BY q.created_at DESC
        LIMIT ?
    """, (limit,))


def get_approved_questions(limit=20):
    """Get approved questions."""
    return query_db("""
        SELECT q.*, cn.name as node_name, t.name as topic_name
        FROM questions q
        JOIN curriculum_nodes cn ON q.curriculum_node_id = cn.id
        JOIN topics t ON cn.topic_id = t.id
        WHERE q.test_status = 'approved'
        ORDER BY q.created_at DESC
        LIMIT ?
    """, (limit,))


def get_question_stats():
    """Get question counts by status."""
    stats = query_db("""
        SELECT test_status, COUNT(*) as count
        FROM questions
        GROUP BY test_status
    """)
    return {row['test_status']: row['count'] for row in stats}


@admin_bp.route('/')
def index():
    """Admin dashboard."""
    stats = get_question_stats()
    pending = get_pending_questions(limit=10)
    return render_template('admin/index.html', stats=stats, pending=pending)


@admin_bp.route('/questions')
def questions():
    """List questions by status."""
    status = request.args.get('status', 'pending_review')
    if status == 'pending_review':
        questions_list = get_pending_questions(limit=50)
    elif status == 'rejected':
        questions_list = get_rejected_questions(limit=50)
    elif status == 'approved':
        questions_list = get_approved_questions(limit=50)
    else:
        questions_list = []

    stats = get_question_stats()
    return render_template('admin/questions.html',
                          questions=questions_list,
                          status=status,
                          stats=stats)


@admin_bp.route('/question/<int:question_id>')
def question_detail(question_id):
    """View a single question in student view."""
    question = get_by_id(question_id)
    if not question:
        flash('Question not found', 'error')
        return redirect(url_for('admin.questions'))

    node = get_node_by_id(question['curriculum_node_id'])
    topic = get_topic_by_id(node['topic_id']) if node else None

    # Parse options
    options = []
    if question['options']:
        try:
            options = json.loads(question['options'])
        except (json.JSONDecodeError, TypeError, ValueError):
            options = []

    return render_template('admin/question_detail.html',
                          question=question,
                          node=node,
                          topic=topic,
                          options=options)


@admin_bp.route('/question/<int:question_id>/approve', methods=['POST'])
def approve_question(question_id):
    """Approve a question for production use."""
    question = get_by_id(question_id)
    if not question:
        flash('Question not found', 'error')
        return redirect(url_for('admin.questions'))

    execute_db(
        "UPDATE questions SET test_status = 'approved' WHERE id = ?",
        (question_id,)
    )
    flash(f'Question {question_id} approved!', 'success')
    return redirect(url_for('admin.question_detail', question_id=question_id))


@admin_bp.route('/question/<int:question_id>/reject', methods=['POST'])
def reject_question(question_id):
    """Reject a question."""
    reason = request.form.get('reason', 'Manual rejection')
    question = get_by_id(question_id)
    if not question:
        flash('Question not found', 'error')
        return redirect(url_for('admin.questions'))

    execute_db(
        "UPDATE questions SET test_status = 'rejected', validation_error = ? WHERE id = ?",
        (reason, question_id)
    )
    flash(f'Question {question_id} rejected: {reason}', 'warning')
    return redirect(url_for('admin.question_detail', question_id=question_id))


@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    """Delete a question completely."""
    execute_db("DELETE FROM questions WHERE id = ?", (question_id,))
    flash(f'Question {question_id} deleted', 'info')
    return redirect(url_for('admin.questions'))


@admin_bp.route('/question/<int:question_id>/api')
def question_api(question_id):
    """Get question as JSON for API testing."""
    question = get_by_id(question_id)
    if not question:
        return jsonify({'error': 'Not found'}), 404

    node = get_node_by_id(question['curriculum_node_id'])

    # Parse options
    options = []
    if question['options']:
        try:
            options = json.loads(question['options'])
        except (json.JSONDecodeError, TypeError, ValueError):
            options = []

    return jsonify({
        'id': question['id'],
        'question': question['content'],
        'question_type': question['question_type'],
        'options': options,
        'correct_answer': question['correct_answer'],
        'explanation': question['explanation'],
        'difficulty': question['difficulty'],
        'node_name': node['name'] if node else None,
        'test_status': question['test_status'],
    })


@admin_bp.route('/stats')
def stats():
    """Get question generation stats."""
    stats = get_question_stats()

    # Get nodes coverage
    coverage = query_db("""
        SELECT
            t.id as topic_id,
            t.name as topic_name,
            COUNT(DISTINCT cn.id) as total_nodes,
            COUNT(DISTINCT q.id) as total_questions,
            COUNT(DISTINCT CASE WHEN q.test_status = 'approved' THEN q.id END) as approved_questions
        FROM topics t
        JOIN curriculum_nodes cn ON cn.topic_id = t.id
        LEFT JOIN questions q ON q.curriculum_node_id = cn.id
        GROUP BY t.id
        ORDER BY t.name
    """)

    return jsonify({
        'stats': stats,
        'coverage': [dict(row) for row in coverage]
    })
