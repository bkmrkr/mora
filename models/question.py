"""CRUD for questions table."""
from db.database import query_db, execute_db


def get_by_id(question_id):
    return query_db("SELECT * FROM questions WHERE id=?", (question_id,), one=True)


def get_for_skill(skill_id, limit=10):
    """Get questions for a skill, random order."""
    return query_db(
        """SELECT * FROM questions WHERE skill_id=?
           ORDER BY RANDOM() LIMIT ?""",
        (skill_id, limit),
    )


def create(skill_id, content, question_type, options, correct_answer,
           explanation=None, difficulty=None, template_id=None):
    return execute_db(
        """INSERT INTO questions
           (skill_id, content, question_type, options, correct_answer,
            explanation, difficulty, template_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (skill_id, content, question_type, options, correct_answer,
         explanation, difficulty, template_id),
    )
