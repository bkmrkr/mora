"""Dashboard routes — progress tracking per student."""
from flask import Blueprint, render_template, request

from models import student as student_model
from models import student_skill as skill_model
from models import attempt as attempt_model
from models import session as session_model
from models import curriculum_node as node_model
from models import topic as topic_model
from engine import elo

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """List all students with summary stats."""
    students = student_model.get_all()
    student_stats = []
    for s in students:
        total = attempt_model.count_for_student(s['id'])
        all_skills = skill_model.get_for_student(s['id'])
        mastered = sum(1 for sk in all_skills if elo.is_mastered(sk['mastery_level']))
        student_stats.append({
            'student': s,
            'total_attempts': total,
            'mastered_nodes': mastered,
            'in_progress': len(all_skills) - mastered,
        })
    return render_template('dashboard/index.html', student_stats=student_stats)


@dashboard_bp.route('/<int:student_id>')
def overview(student_id):
    """Per-student skill tree with mastery, recent sessions."""
    student = student_model.get_by_id(student_id)
    if not student:
        return render_template('dashboard/index.html', student_stats=[])

    all_skills = skill_model.get_for_student(student_id)
    skills_by_node = {s['curriculum_node_id']: s for s in all_skills}

    topics = topic_model.get_all()
    topic_tree = []
    for t in topics:
        nodes = node_model.get_for_topic(t['id'])
        node_list = []
        for n in nodes:
            sk = skills_by_node.get(n['id'])
            node_list.append({
                'name': n['name'],
                'skill_rating': round(sk['skill_rating'], 1) if sk else 800,
                'mastery_level': round(sk['mastery_level'], 3) if sk else 0,
                'mastery_pct': round((sk['mastery_level'] if sk else 0) * 100),
                'mastered': elo.is_mastered(sk['mastery_level']) if sk else False,
                'total_attempts': sk['total_attempts'] if sk else 0,
            })
        topic_tree.append({'name': t['name'], 'nodes': node_list})

    sessions = session_model.get_for_student(student_id, limit=20)

    return render_template(
        'dashboard/overview.html',
        student=student,
        topic_tree=topic_tree,
        sessions=sessions,
    )


@dashboard_bp.route('/<int:student_id>/history')
def history(student_id):
    """Paginated attempt history."""
    student = student_model.get_by_id(student_id)
    if not student:
        return render_template('dashboard/index.html', student_stats=[])

    page = int(request.args.get('page', 1))
    per_page = 30
    offset = (page - 1) * per_page
    attempts = attempt_model.get_for_student(student_id, limit=per_page, offset=offset)
    total = attempt_model.count_for_student(student_id)
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        'dashboard/history.html',
        student=student,
        attempts=attempts,
        page=page,
        total_pages=total_pages,
    )
