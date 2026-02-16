"""Dashboard routes — grade progression per student."""
from flask import Blueprint, render_template, redirect, url_for

from models import student as student_model
from models import attempt as attempt_model
from models import session as session_model
from models.progress import get_for_student
from curriculum.skills import get_skills_for_grade, get_skill, SKILLS
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
        # Determine current grade (highest grade with any non-mastered, unlocked skill)
        progress_map = {sk['skill_id']: sk for sk in all_skills}
        current_grade = 1
        for grade in [4, 3, 2, 1]:
            grade_skills = get_skills_for_grade(grade)
            has_activity = any(
                progress_map.get(gs['id'], {}).get('total_attempts', 0) > 0
                for gs in grade_skills
            )
            if has_activity:
                current_grade = grade
                break
        student_stats.append({
            'student': s,
            'total_attempts': total,
            'mastered_skills': mastered,
            'total_skills': 40,
            'current_grade': current_grade,
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
            prereqs_met_count = 0
            if locked:
                for pid in prereqs:
                    ps = get_skill(pid)
                    pid_mastered = elo.is_mastered(
                        progress_by_skill.get(pid, {}).get('mastery_level', 0))
                    if pid_mastered:
                        prereqs_met_count += 1
                    elif ps:
                        prereq_names.append(ps['name'])
            skill_list.append({
                'name': s['name'],
                'skill_rating': round(prog['skill_rating'], 1) if prog else 800,
                'mastery_pct': round(mastery * 100),
                'mastered': is_mastered,
                'total_attempts': prog['total_attempts'] if prog else 0,
                'locked': locked,
                'prereq_names': prereq_names,
                'prereqs_met_count': prereqs_met_count,
                'prereqs_total': len(prereqs),
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

    # Focus skill: unmastered skill closest to mastery threshold
    focus_skill = None
    best_mastery = -1
    for sid, sinfo in SKILLS.items():
        prog = progress_by_skill.get(sid)
        mastery = prog['mastery_level'] if prog else 0.0
        if not elo.is_mastered(mastery) and mastery > best_mastery:
            prereqs_met = all(
                elo.is_mastered(progress_by_skill.get(pid, {}).get('mastery_level', 0))
                for pid in sinfo.get('prerequisites', [])
            )
            if prereqs_met or not sinfo.get('prerequisites'):
                best_mastery = mastery
                focus_skill = {
                    'name': sinfo['name'],
                    'grade': sinfo['grade'],
                    'mastery_pct': round(mastery * 100),
                }

    # Practice streak
    streak_days, practiced_today = session_model.get_practice_streak(student_id)

    # Overall stats
    total_questions = sum(s['total_questions'] or 0 for s in sessions)
    total_correct = sum(s['total_correct'] or 0 for s in sessions)
    overall_accuracy = round(total_correct / total_questions * 100) if total_questions > 0 else 0

    # Accuracy trend for chart (oldest first, last 10 sessions)
    accuracy_trend = []
    for s in reversed(sessions[:10]):
        q = s['total_questions'] or 0
        c = s['total_correct'] or 0
        acc = round(c / q * 100) if q > 0 else 0
        accuracy_trend.append({
            'accuracy': acc,
            'questions': q,
            'date': s['started_at'][:10] if s.get('started_at') else '',
        })

    return render_template(
        'dashboard/overview.html',
        student=student,
        grade_tree=grade_tree,
        grade_summary=grade_summary,
        total_mastered=total_mastered,
        total_skills=total_skills,
        sessions=sessions,
        focus_skill=focus_skill,
        streak_days=streak_days,
        practiced_today=practiced_today,
        total_questions=total_questions,
        overall_accuracy=overall_accuracy,
        accuracy_trend=accuracy_trend,
    )
