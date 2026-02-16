"""Dashboard routes — grade progression per student."""
from flask import Blueprint, render_template, redirect, url_for

from models import student as student_model
from models import attempt as attempt_model
from models import session as session_model
from models.progress import get_for_student
from curriculum.skills import get_skills_for_grade, get_skill
from engine import elo

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    students = student_model.get_all()
    student_stats = []
    for s in students:
        total = attempt_model.count_for_student(s['id'])
        all_skills = get_for_student(s['id'])
        mastered = sum(1 for sk in all_skills if elo.is_mastered(sk['mastery_level']))
        student_stats.append({
            'student': s,
            'total_attempts': total,
            'mastered_skills': mastered,
            'in_progress': len(all_skills) - mastered,
        })
    return render_template('dashboard/index.html', student_stats=student_stats)


@dashboard_bp.route('/<int:student_id>')
def overview(student_id):
    student = student_model.get_by_id(student_id)
    if not student:
        return redirect(url_for('dashboard.index'))

    all_progress = get_for_student(student_id)
    progress_by_skill = {p['skill_id']: p for p in all_progress}

    grade_tree = []
    for grade in [1, 2, 3, 4]:
        skills = get_skills_for_grade(grade)
        skill_list = []
        for s in skills:
            prog = progress_by_skill.get(s['id'])
            mastery = prog['mastery_level'] if prog else 0.0
            # Check if prerequisites are met
            prereqs = s.get('prerequisites', [])
            prereqs_met = all(
                elo.is_mastered(progress_by_skill.get(pid, {}).get('mastery_level', 0))
                for pid in prereqs
            )
            is_mastered = elo.is_mastered(mastery)
            locked = bool(prereqs) and not prereqs_met and not is_mastered
            prereq_names = []
            if locked:
                for pid in prereqs:
                    ps = get_skill(pid)
                    if ps and not elo.is_mastered(
                            progress_by_skill.get(pid, {}).get('mastery_level', 0)):
                        prereq_names.append(ps['name'])
            skill_list.append({
                'name': s['name'],
                'skill_rating': round(prog['skill_rating'], 1) if prog else 800,
                'mastery_pct': round(mastery * 100),
                'mastered': is_mastered,
                'total_attempts': prog['total_attempts'] if prog else 0,
                'locked': locked,
                'prereq_names': prereq_names,
            })
        grade_tree.append({'grade': grade, 'skills': skill_list})

    # Grade summary for overview bar
    grade_summary = []
    total_mastered = 0
    total_skills = 0
    for gt in grade_tree:
        mastered = sum(1 for s in gt['skills'] if s['mastered'])
        total = len(gt['skills'])
        total_mastered += mastered
        total_skills += total
        grade_summary.append({
            'grade': gt['grade'],
            'mastered': mastered,
            'total': total,
            'complete': mastered == total,
        })

    sessions = session_model.get_for_student(student_id, limit=20)
    sessions = [s for s in sessions if s['total_questions']]

    return render_template(
        'dashboard/overview.html',
        student=student,
        grade_tree=grade_tree,
        grade_summary=grade_summary,
        total_mastered=total_mastered,
        total_skills=total_skills,
        sessions=sessions,
    )
