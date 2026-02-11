"""CRUD for attempts table."""
from db.database import query_db, execute_db


def create(question_id, student_id, session_id, answer_given, is_correct,
           partial_score=None, response_time_seconds=None):
    return execute_db(
        """INSERT INTO attempts
           (question_id, student_id, session_id, answer_given, is_correct,
            partial_score, response_time_seconds)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (question_id, student_id, session_id, answer_given, is_correct,
         partial_score, response_time_seconds),
    )


def get_recent(student_id, limit=30):
    """Last N attempts with question and node info."""
    return query_db(
        """SELECT a.*, q.content, q.correct_answer, q.difficulty,
                  q.curriculum_node_id, q.question_type, q.options
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.student_id=?
           ORDER BY a.timestamp DESC
           LIMIT ?""",
        (student_id, limit),
    )


def get_recent_for_node(student_id, node_id, limit=30):
    return query_db(
        """SELECT a.*, q.curriculum_node_id
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.student_id=? AND q.curriculum_node_id=?
           ORDER BY a.timestamp DESC
           LIMIT ?""",
        (student_id, node_id, limit),
    )


def get_for_session(session_id):
    """All attempts in a session with question info."""
    return query_db(
        """SELECT a.*, q.content, q.correct_answer, q.curriculum_node_id,
                  q.question_type, q.options
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.session_id=?
           ORDER BY a.timestamp""",
        (session_id,),
    )


def get_correct_texts(student_id):
    """All distinct question texts the student answered correctly (lifetime).

    Used for global dedup — never re-ask a mastered question.
    """
    rows = query_db(
        """SELECT DISTINCT q.content
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           WHERE a.student_id=? AND a.is_correct=1""",
        (student_id,),
    )
    return {r['content'] for r in rows}


def count_for_student(student_id):
    row = query_db(
        "SELECT COUNT(*) as cnt FROM attempts WHERE student_id=?",
        (student_id,), one=True,
    )
    return row['cnt'] if row else 0


def get_for_student(student_id, limit=30, offset=0):
    return query_db(
        """SELECT a.*, q.content, q.correct_answer, q.curriculum_node_id,
                  cn.name as node_name
           FROM attempts a
           JOIN questions q ON a.question_id = q.id
           LEFT JOIN curriculum_nodes cn ON q.curriculum_node_id = cn.id
           WHERE a.student_id=?
           ORDER BY a.timestamp DESC
           LIMIT ? OFFSET ?""",
        (student_id, limit, offset),
    )
