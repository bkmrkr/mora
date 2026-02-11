"""CRUD for curriculum_nodes table."""
import json

from db.database import query_db, execute_db


def get_by_id(node_id):
    return query_db(
        "SELECT * FROM curriculum_nodes WHERE id=?", (node_id,), one=True
    )


def get_for_topic(topic_id):
    return query_db(
        "SELECT * FROM curriculum_nodes WHERE topic_id=? ORDER BY order_index",
        (topic_id,),
    )


def create(topic_id, name, description=None, order_index=0,
           prerequisites='[]', mastery_threshold=0.75):
    return execute_db(
        """INSERT INTO curriculum_nodes
           (topic_id, name, description, order_index, prerequisites, mastery_threshold)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (topic_id, name, description, order_index, prerequisites, mastery_threshold),
    )


def get_prerequisites(node_id):
    row = get_by_id(node_id)
    if not row or not row['prerequisites']:
        return []
    return json.loads(row['prerequisites'])
