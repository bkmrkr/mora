"""Model for question quality reports."""
from db.database import execute_db, query_db


def create(question_id, student_id=None, reason='', details=''):
    """Create a new question report."""
    execute_db(
        'INSERT INTO question_reports (question_id, student_id, reason, details) VALUES (?, ?, ?, ?)',
        (question_id, student_id, reason, details),
    )


def get_by_question(question_id):
    """Get all reports for a question."""
    return query_db(
        'SELECT * FROM question_reports WHERE question_id = ? ORDER BY created_at DESC',
        (question_id,),
        one=False
    )


def mark_as_rejected(question_id, reason=''):
    """Mark a question as rejected/bad."""
    execute_db(
        'UPDATE questions SET is_rejected = 1, rejection_reason = ? WHERE id = ?',
        (reason, question_id),
    )


def get_rejected_questions():
    """Get all rejected questions."""
    return query_db(
        'SELECT * FROM questions WHERE is_rejected = 1 ORDER BY created_at DESC',
        one=False
    )
