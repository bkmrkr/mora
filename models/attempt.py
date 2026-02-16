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
