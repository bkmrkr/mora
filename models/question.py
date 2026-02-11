"""CRUD for questions table."""
from db.database import query_db, execute_db


def get_by_id(question_id):
    return query_db("SELECT * FROM questions WHERE id=?", (question_id,), one=True)


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
