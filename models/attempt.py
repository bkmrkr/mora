"""CRUD for attempts table."""
from db.database import query_db, execute_db


def create(question_id, student_id, session_id, skill_id, answer_given,
           is_correct, response_time_seconds=None,
           skill_rating_before=None, skill_rating_after=None):
    return execute_db(
        """INSERT INTO attempts
           (question_id, student_id, session_id, skill_id, answer_given,
            is_correct, response_time_seconds,
            skill_rating_before, skill_rating_after)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (question_id, student_id, session_id, skill_id, answer_given,
         is_correct, response_time_seconds,
         skill_rating_before, skill_rating_after),
    )


def get_recent(student_id, limit=30):
    """Last N attempts with question info."""
    return query_db(
        """SELECT a.*, q.content, q.correct_answer, q.difficulty,
                  q.skill_id as q_skill_id, q.question_type, q.options
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.student_id=?
           ORDER BY a.timestamp DESC
           LIMIT ?""",
        (student_id, limit),
    )


def get_recent_for_skill(student_id, skill_id, limit=30):
    return query_db(
        """SELECT a.*
           FROM attempts a
           WHERE a.student_id=? AND a.skill_id=?
           ORDER BY a.timestamp DESC
           LIMIT ?""",
        (student_id, skill_id, limit),
    )


def get_for_session(session_id):
    """All attempts in a session with question info."""
    return query_db(
        """SELECT a.*, q.content, q.correct_answer, q.skill_id as q_skill_id,
                  q.question_type, q.options
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.session_id=?
           ORDER BY a.timestamp""",
        (session_id,),
    )


def count_for_student(student_id):
    row = query_db(
        "SELECT COUNT(*) as cnt FROM attempts WHERE student_id=?",
        (student_id,), one=True,
    )
    return row['cnt'] if row else 0


def get_personal_records(student_id):
    """Compute personal records: best streak, fastest correct, best session accuracy."""
    # Best streak: longest consecutive correct answers
    all_attempts = query_db(
        """SELECT is_correct FROM attempts
           WHERE student_id=? ORDER BY timestamp""",
        (student_id,),
    )
    best_streak = 0
    current = 0
    for a in all_attempts:
        if a['is_correct']:
            current += 1
            best_streak = max(best_streak, current)
        else:
            current = 0

    # Fastest correct answer
    fastest_row = query_db(
        """SELECT MIN(response_time_seconds) as fastest
           FROM attempts
           WHERE student_id=? AND is_correct=1
           AND response_time_seconds > 0""",
        (student_id,), one=True,
    )
    fastest_correct = fastest_row['fastest'] if fastest_row and fastest_row['fastest'] else None

    # Best session accuracy (min 5 questions)
    best_acc_row = query_db(
        """SELECT MAX(CAST(total_correct AS REAL) / total_questions * 100) as best_acc
           FROM sessions
           WHERE student_id=? AND total_questions >= 5 AND ended_at IS NOT NULL""",
        (student_id,), one=True,
    )
    best_accuracy = round(best_acc_row['best_acc'], 1) if best_acc_row and best_acc_row['best_acc'] else None

    return {
        'best_streak': best_streak,
        'fastest_correct': round(fastest_correct, 1) if fastest_correct else None,
        'best_accuracy': best_accuracy,
    }


def get_since(student_id, since_date):
    """All attempts for a student since a date (YYYY-MM-DD string)."""
    return query_db(
        """SELECT a.*, q.skill_id as q_skill_id
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.student_id=? AND a.timestamp >= ?
           ORDER BY a.timestamp""",
        (student_id, since_date),
    )
