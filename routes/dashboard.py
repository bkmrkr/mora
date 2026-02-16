"""Dashboard routes — grade progression per student."""
from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for

from models import student as student_model
from models import attempt as attempt_model
from models import session as session_model
from models.progress import get_for_student
from curriculum.skills import get_skills_for_grade, get_skill, SKILLS
from engine import elo

dashboard_bp = Blueprint('dashboard', __name__)


def _parse_num(s):
    """Parse a string as a number (int, float, or fraction)."""
    s = str(s).strip()
    try:
        if '/' in s:
            parts = s.split('/')
            return float(parts[0]) / float(parts[1])
        return float(s.replace(',', ''))
    except (ValueError, ZeroDivisionError, IndexError):
        return None


def _analyze_mistakes(student_id):
    """Analyze recent wrong answers to identify mistake patterns."""
    recent = attempt_model.get_recent(student_id, limit=50)
    wrong = [a for a in recent if not a['is_correct']
             and a.get('answer_given') and a.get('correct_answer')]

    if len(wrong) < 3:
        return []

    counts = {
        'off_by_one': 0,
        'place_value': 0,
        'digit_swap': 0,
        'rushing': 0,
    }

    for a in wrong:
        sa = _parse_num(a['answer_given'])
        ca = _parse_num(a['correct_answer'])
        if sa is not None and ca is not None:
            diff = abs(sa - ca)
            if diff == 1:
                counts['off_by_one'] += 1
            elif diff in (10, 100, 1000):
                counts['place_value'] += 1
            # Digit swap check
            ss, cs = a['answer_given'].strip(), a['correct_answer'].strip()
            if (len(ss) == 2 and len(cs) == 2
                    and ss[0] == cs[1] and ss[1] == cs[0]):
                counts['digit_swap'] += 1
        rt = a.get('response_time_seconds')
        if rt and 0 < rt < 2:
            counts['rushing'] += 1  # already in wrong-only list

    patterns = []
    total_wrong = len(wrong)
    if counts['off_by_one'] >= 3:
        pct = round(counts['off_by_one'] / total_wrong * 100)
        patterns.append({
            'icon': '&#128161;',
            'label': 'Off-by-one errors',
            'desc': f'{counts["off_by_one"]} times in last {total_wrong} mistakes ({pct}%)',
            'tip': 'Try counting on fingers or a number line to double-check.',
        })
    if counts['place_value'] >= 2:
        pct = round(counts['place_value'] / total_wrong * 100)
        patterns.append({
            'icon': '&#127922;',
            'label': 'Place value mix-ups',
            'desc': f'{counts["place_value"]} errors off by 10, 100, or 1000',
            'tip': 'Practice identifying tens, hundreds, and thousands places.',
        })
    if counts['digit_swap'] >= 2:
        patterns.append({
            'icon': '&#128260;',
            'label': 'Digit reversals',
            'desc': f'{counts["digit_swap"]} times digits were swapped (e.g. 21 vs 12)',
            'tip': 'Read the answer back to yourself before submitting.',
        })
    if counts['rushing'] >= 3:
        pct = round(counts['rushing'] / total_wrong * 100)
        patterns.append({
            'icon': '&#9200;',
            'label': 'Rushing',
            'desc': f'{counts["rushing"]} wrong answers in under 2 seconds',
            'tip': 'Slow down and read the question carefully before answering.',
        })

    return patterns[:3]  # top 3 patterns


MATH_LEVELS = [
    (0, 'Starter', 5),
    (5, 'Explorer', 10),
    (10, 'Learner', 15),
    (15, 'Scholar', 20),
    (20, 'Expert', 25),
    (25, 'Champion', 30),
    (30, 'Master', 35),
    (35, 'Grandmaster', 40),
    (40, 'Legend', 40),
]


def _compute_math_level(mastered_count):
    """Compute math level from number of mastered skills."""
    level_name = 'Starter'
    next_threshold = 5
    for threshold, name, next_t in reversed(MATH_LEVELS):
        if mastered_count >= threshold:
            level_name = name
            next_threshold = next_t
            break
    progress_in_level = mastered_count - (next_threshold - 5) if next_threshold > 5 else mastered_count
    level_size = 5
    pct = min(round(progress_in_level / level_size * 100), 100) if level_size > 0 else 100
    return {
        'name': level_name,
        'mastered': mastered_count,
        'next_at': next_threshold,
        'progress_pct': pct,
    }


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
        _, practiced_today = session_model.get_practice_streak(s['id'])
        level = _compute_math_level(mastered)
        student_stats.append({
            'student': s,
            'total_attempts': total,
            'mastered_skills': mastered,
            'total_skills': 40,
            'current_grade': current_grade,
            'practiced_today': practiced_today,
            'level_name': level['name'],
        })
    return render_template('dashboard/index.html', student_stats=student_stats)


@dashboard_bp.route('/<int:student_id>')
def overview(student_id):
    student = student_model.get_by_id(student_id)
    if not student:
        return redirect(url_for('dashboard.index'))

    all_progress = get_for_student(student_id)
    progress_by_skill = {p['skill_id']: p for p in all_progress}

    # Fetch recent attempts for sparklines (one query, group by skill)
    recent_attempts = attempt_model.get_recent(student_id, limit=200)
    sparkline_map = {}  # skill_id -> list of bools (oldest first, max 5)
    for a in reversed(recent_attempts):  # reversed = oldest first
        sid = a.get('q_skill_id') or a.get('skill_id', '')
        if sid not in sparkline_map:
            sparkline_map[sid] = []
        if len(sparkline_map[sid]) < 5:
            sparkline_map[sid].append(bool(a['is_correct']))

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
                'sparkline': sparkline_map.get(s['id'], []),
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

    # Math level based on total mastered skills
    math_level = _compute_math_level(total_mastered)

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

    # Mastery timeline: recently mastered skills with dates
    mastery_timeline = []
    for sid, prog in progress_by_skill.items():
        if elo.is_mastered(prog['mastery_level']):
            skill_info = get_skill(sid)
            if skill_info:
                mastery_timeline.append({
                    'name': skill_info['name'],
                    'grade': skill_info['grade'],
                    'date': prog['last_updated'][:10] if prog.get('last_updated') else '',
                })
    # Sort by date descending (most recent first), limit to 8
    mastery_timeline.sort(key=lambda x: x['date'], reverse=True)
    mastery_timeline = mastery_timeline[:8]

    # Achievement badges — computed from existing data
    badges = []
    if total_mastered >= 1:
        badges.append({'icon': '&#11088;', 'name': 'First Mastery', 'desc': 'Mastered your first skill'})
    if total_mastered >= 10:
        badges.append({'icon': '&#127775;', 'name': 'Rising Star', 'desc': '10 skills mastered'})
    if total_mastered >= 20:
        badges.append({'icon': '&#128293;', 'name': 'Halfway There', 'desc': '20 skills mastered'})
    if total_mastered >= 40:
        badges.append({'icon': '&#127942;', 'name': 'Legend', 'desc': 'All 40 skills mastered!'})
    for gs in grade_summary:
        if gs['complete']:
            badges.append({'icon': '&#127891;', 'name': f'Grade {gs["grade"]} Complete',
                           'desc': f'Mastered all Grade {gs["grade"]} skills'})
    # Perfect session badge (any session with 10+ questions and 100% accuracy)
    perfect = any(
        (s['total_questions'] or 0) >= 10 and s['total_correct'] == s['total_questions']
        for s in sessions
    )
    if perfect:
        badges.append({'icon': '&#128175;', 'name': 'Perfect Session', 'desc': '100% on 10+ questions'})
    # Speed badge (check if any session has avg time < 4s)
    for s in sessions:
        s_attempts = attempt_model.get_for_session(s['id'])
        times = [a['response_time_seconds'] for a in s_attempts
                 if a.get('response_time_seconds') and a['response_time_seconds'] > 0
                 and a['is_correct']]
        if len(times) >= 5 and sum(times) / len(times) < 4:
            badges.append({'icon': '&#9889;', 'name': 'Speed Demon', 'desc': 'Avg under 4s on correct answers'})
            break
    if streak_days >= 3:
        badges.append({'icon': '&#128170;', 'name': 'Streak Star', 'desc': f'{streak_days} day practice streak'})
    if total_questions >= 100:
        badges.append({'icon': '&#128218;', 'name': 'Century', 'desc': '100+ questions answered'})
    if total_questions >= 500:
        badges.append({'icon': '&#127793;', 'name': 'Dedicated', 'desc': '500+ questions answered'})

    # "This Week" summary
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    week_attempts = attempt_model.get_since(student_id, week_start)
    week_summary = None
    if week_attempts:
        week_total = len(week_attempts)
        week_correct = sum(1 for a in week_attempts if a['is_correct'])
        week_accuracy = round(week_correct / week_total * 100) if week_total > 0 else 0
        week_skills = set(a['skill_id'] for a in week_attempts)
        # XP this week
        week_xp = 0
        for a in week_attempts:
            before = a.get('skill_rating_before') or 0
            after = a.get('skill_rating_after') or 0
            diff = after - before
            if diff > 0:
                week_xp += diff
        # New masteries this week (skills whose last_updated is this week)
        week_new_masteries = []
        for item in mastery_timeline:
            if item['date'] >= week_start:
                week_new_masteries.append(item['name'])
        week_summary = {
            'total': week_total,
            'correct': week_correct,
            'accuracy': week_accuracy,
            'skills_practiced': len(week_skills),
            'xp': round(week_xp, 1),
            'new_masteries': week_new_masteries,
        }

    # Practice heatmap: last 28 days, aligned to start on Monday
    practice_days = session_model.get_practice_days(student_id, days=35)
    today = date.today()
    raw_start = today - timedelta(days=27)
    # Align to Monday (weekday 0 = Monday)
    start_date = raw_start - timedelta(days=raw_start.weekday())
    total_days = (today - start_date).days + 1
    # Pad to complete weeks
    total_days = ((total_days + 6) // 7) * 7
    heatmap = []
    for i in range(total_days):
        d = start_date + timedelta(days=i)
        day_str = d.isoformat()
        is_future = d > today
        count = practice_days.get(day_str, 0) if not is_future else 0
        heatmap.append({
            'date': day_str,
            'day': d.day,
            'count': count,
            'level': min(count // 5, 3) if count > 0 else 0,
            'is_today': d == today,
            'is_future': is_future,
        })
    heatmap_weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

    # Mistake pattern analysis from recent wrong answers
    mistake_patterns = _analyze_mistakes(student_id)

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
        math_level=math_level,
        mastery_timeline=mastery_timeline,
        badges=badges,
        week_summary=week_summary,
        heatmap=heatmap,
        heatmap_weekdays=heatmap_weekdays,
        mistake_patterns=mistake_patterns,
    )


@dashboard_bp.route('/<int:student_id>/session/<session_id>')
def session_detail(student_id, session_id):
    student = student_model.get_by_id(student_id)
    if not student:
        return redirect(url_for('dashboard.index'))

    sess = session_model.get_by_id(session_id)
    if not sess or sess['student_id'] != student_id:
        return redirect(url_for('dashboard.overview', student_id=student_id))

    attempts = attempt_model.get_for_session(session_id)

    # Build timeline entries with skill names
    timeline = []
    for i, a in enumerate(attempts):
        skill_info = get_skill(a['skill_id'])
        skill_name = skill_info['name'] if skill_info else a['skill_id']
        resp_time = a.get('response_time_seconds') or 0
        timeline.append({
            'num': i + 1,
            'skill_name': skill_name,
            'is_correct': bool(a['is_correct']),
            'answer_given': a.get('answer_given', ''),
            'correct_answer': a.get('correct_answer', ''),
            'content': a.get('content', ''),
            'response_time': round(resp_time, 1) if resp_time else None,
        })

    total_q = len(attempts)
    total_c = sum(1 for a in attempts if a['is_correct'])
    accuracy = round(total_c / total_q * 100) if total_q > 0 else 0
    times = [a['response_time_seconds'] for a in attempts
             if a.get('response_time_seconds') and a['response_time_seconds'] > 0]
    avg_time = round(sum(times) / len(times), 1) if times else None

    # Compute best streak
    best_streak = 0
    current_streak = 0
    for a in attempts:
        if a['is_correct']:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

    return render_template(
        'dashboard/session_detail.html',
        student=student,
        sess=sess,
        timeline=timeline,
        total_questions=total_q,
        total_correct=total_c,
        accuracy=accuracy,
        avg_time=avg_time,
        best_streak=best_streak,
    )
