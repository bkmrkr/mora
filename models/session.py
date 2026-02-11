"""CRUD for sessions table."""
import uuid

from db.database import query_db, execute_db


def create(student_id, topic_id=None):
    session_id = str(uuid.uuid4())
    execute_db(
        "INSERT INTO sessions (id, student_id, topic_id) VALUES (?, ?, ?)",
        (session_id, student_id, topic_id),
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
                  SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) as correct
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
