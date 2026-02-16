"""CRUD for sessions table."""
import uuid
from datetime import date, timedelta

from db.database import query_db, execute_db


def create(student_id):
    session_id = str(uuid.uuid4())
    execute_db(
        "INSERT INTO sessions (id, student_id) VALUES (?, ?)",
        (session_id, student_id),
    )
    return session_id


def get_by_id(session_id):
    return query_db(
        "SELECT * FROM sessions WHERE id=?", (session_id,), one=True
    )


def end_session(session_id):
    """Compute totals from attempts and mark session as ended."""
    row = query_db(
        """SELECT COUNT(*) as total,
                  COALESCE(SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END), 0) as correct
           FROM attempts WHERE session_id=?""",
        (session_id,), one=True,
    )
    total = row['total'] if row else 0
    correct = row['correct'] if row else 0
    execute_db(
        """UPDATE sessions SET ended_at=CURRENT_TIMESTAMP,
           total_questions=?, total_correct=? WHERE id=?""",
        (total, correct, session_id),
    )


def update_current_question(session_id, question_id):
    execute_db(
        "UPDATE sessions SET current_question_id=? WHERE id=?",
        (question_id, session_id),
    )


def update_last_result(session_id, result_json):
    execute_db(
        "UPDATE sessions SET last_result_json=? WHERE id=?",
        (result_json, session_id),
    )


def get_for_student(student_id, limit=20):
    return query_db(
        """SELECT * FROM sessions WHERE student_id=?
           ORDER BY started_at DESC LIMIT ?""",
        (student_id, limit),
    )


def get_practice_streak(student_id):
    """Count consecutive days of practice ending today or yesterday.

    Returns (streak_days, practiced_today).
    """
    rows = query_db(
        """SELECT DISTINCT DATE(started_at) as day
           FROM sessions WHERE student_id=?
           ORDER BY day DESC""",
        (student_id,),
    )
    if not rows:
        return 0, False

    practice_days = {row['day'] for row in rows}
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    practiced_today = today in practice_days

    # Start counting from today or yesterday
    if today in practice_days:
        check = date.today()
    elif yesterday in practice_days:
        check = date.today() - timedelta(days=1)
    else:
        return 0, False

    streak = 0
    while check.isoformat() in practice_days:
        streak += 1
        check -= timedelta(days=1)

    return streak, practiced_today
