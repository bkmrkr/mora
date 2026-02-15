"""CRUD for student_progress table."""
from db.database import query_db, execute_db
from config.settings import ELO_DEFAULTS


def get(student_id, skill_id):
    """Return progress row, or defaults dict if not yet created."""
    row = query_db(
        "SELECT * FROM student_progress WHERE student_id=? AND skill_id=?",
        (student_id, skill_id), one=True,
    )
    if row:
        return row
    return {
        'student_id': student_id,
        'skill_id': skill_id,
        'skill_rating': ELO_DEFAULTS['initial_skill_rating'],
        'uncertainty': ELO_DEFAULTS['initial_uncertainty'],
        'mastery_level': 0.0,
        'total_attempts': 0,
        'correct_attempts': 0,
    }


def upsert(student_id, skill_id, skill_rating, uncertainty, mastery_level,
           total_attempts, correct_attempts):
    execute_db(
        """INSERT INTO student_progress
           (student_id, skill_id, skill_rating, uncertainty,
            mastery_level, total_attempts, correct_attempts, last_updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(student_id, skill_id) DO UPDATE SET
            skill_rating=excluded.skill_rating,
            uncertainty=excluded.uncertainty,
            mastery_level=excluded.mastery_level,
            total_attempts=excluded.total_attempts,
            correct_attempts=excluded.correct_attempts,
            last_updated=CURRENT_TIMESTAMP""",
        (student_id, skill_id, skill_rating, uncertainty, mastery_level,
         total_attempts, correct_attempts),
    )


def get_for_student(student_id):
    return query_db(
        "SELECT * FROM student_progress WHERE student_id=? ORDER BY skill_id",
        (student_id,),
    )
