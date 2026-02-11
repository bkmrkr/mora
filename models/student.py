"""CRUD for students table."""
from db.database import query_db, execute_db


def get_all():
    return query_db("SELECT * FROM students ORDER BY name")


def get_by_id(student_id):
    return query_db("SELECT * FROM students WHERE id=?", (student_id,), one=True)


def get_by_name(name):
    return query_db("SELECT * FROM students WHERE name=?", (name,), one=True)


def create(name):
    return execute_db("INSERT INTO students (name) VALUES (?)", (name,))
