"""CRUD for topics table."""
from db.database import query_db, execute_db


def get_all():
    return query_db("SELECT * FROM topics ORDER BY name")


def get_by_id(topic_id):
    return query_db("SELECT * FROM topics WHERE id=?", (topic_id,), one=True)


def get_by_name(name):
    return query_db("SELECT * FROM topics WHERE name=?", (name,), one=True)


def create(name, description=None, parent_id=None):
    return execute_db(
        "INSERT INTO topics (name, description, parent_id) VALUES (?, ?, ?)",
        (name, description, parent_id),
    )


def get_children(parent_id):
    return query_db(
        "SELECT * FROM topics WHERE parent_id=? ORDER BY name", (parent_id,)
    )
