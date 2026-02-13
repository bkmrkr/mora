"""CRUD for questions table."""
from db.database import query_db, execute_db


def get_by_id(question_id, approved_only=False):
    """Get a question by ID.

    Args:
        question_id: The question ID
        approved_only: If True, only return approved questions (for student use)
    """
    if approved_only:
        return query_db(
            "SELECT * FROM questions WHERE id=? AND test_status='approved'",
            (question_id,), one=True
        )
    return query_db("SELECT * FROM questions WHERE id=?", (question_id,), one=True)


def get_by_id_approved(question_id):
    """Get an approved question by ID (for student use)."""
    return query_db(
        "SELECT * FROM questions WHERE id=? AND (test_status = 'approved' OR test_status IS NULL)",
        (question_id,), one=True
    )


def get_for_node(curriculum_node_id, limit=10):
    """Get approved questions for a curriculum node (for student use)."""
    return query_db("""
        SELECT * FROM questions
        WHERE curriculum_node_id = ?
        AND (test_status = 'approved' OR test_status IS NULL)
        ORDER BY RANDOM()
        LIMIT ?
    """, (curriculum_node_id, limit))


def create(curriculum_node_id, content, question_type, options, correct_answer,
           explanation=None, difficulty=None, estimated_p_correct=None,
           generated_prompt=None, model_used=None):
    return execute_db(
        """INSERT INTO questions
           (curriculum_node_id, content, question_type, options, correct_answer,
            explanation, difficulty, estimated_p_correct, generated_prompt, model_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (curriculum_node_id, content, question_type, options, correct_answer,
         explanation, difficulty, estimated_p_correct, generated_prompt, model_used),
    )


def update_status(question_id, status):
    """Update the test_status of a question."""
    execute_db(
        "UPDATE questions SET test_status = ? WHERE id = ?",
        (status, question_id)
    )
