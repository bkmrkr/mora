"""Tests for models layer — basic CRUD operations."""
from models import student, topic, curriculum_node, question, attempt, student_skill, session


def test_create_student():
    sid = student.create("Alice")
    s = student.get_by_id(sid)
    assert s['name'] == "Alice"


def test_get_by_name():
    student.create("Bob")
    s = student.get_by_name("Bob")
    assert s is not None
    assert s['name'] == "Bob"


def test_get_all_students():
    student.create("Alice")
    student.create("Bob")
    all_s = student.get_all()
    assert len(all_s) == 2


def test_create_topic():
    tid = topic.create("Calculus", "Intro to calculus")
    t = topic.get_by_id(tid)
    assert t['name'] == "Calculus"


def test_create_curriculum_node():
    tid = topic.create("Math")
    nid = curriculum_node.create(tid, "Derivatives", "Intro to derivatives", 1)
    n = curriculum_node.get_by_id(nid)
    assert n['name'] == "Derivatives"
    assert n['topic_id'] == tid


def test_get_nodes_for_topic():
    tid = topic.create("Physics")
    curriculum_node.create(tid, "Newton's Laws", order_index=1)
    curriculum_node.create(tid, "Kinematics", order_index=0)
    nodes = curriculum_node.get_for_topic(tid)
    assert len(nodes) == 2
    assert nodes[0]['name'] == "Kinematics"  # Ordered by order_index


def test_create_session():
    sid = student.create("Alice")
    sess_id = session.create(sid)
    sess = session.get_by_id(sess_id)
    assert sess['student_id'] == sid


def test_student_skill_defaults():
    sk = student_skill.get(999, 999)
    assert sk['skill_rating'] == 800.0
    assert sk['uncertainty'] == 350.0  # Matches spec: initial_uncertainty


def test_student_skill_upsert():
    sid = student.create("Alice")
    tid = topic.create("Math")
    nid = curriculum_node.create(tid, "Algebra")
    student_skill.upsert(sid, nid, 1050.0, 280.0, 0.6, 10, 7)
    sk = student_skill.get(sid, nid)
    assert sk['skill_rating'] == 1050.0
    assert sk['total_attempts'] == 10


def test_create_question_and_attempt():
    sid = student.create("Alice")
    tid = topic.create("Math")
    nid = curriculum_node.create(tid, "Algebra")
    sess_id = session.create(sid)
    qid = question.create(nid, "What is 2+2?", "mcq", '["3","4","5","6"]', "4")
    aid = attempt.create(qid, sid, sess_id, "4", 1)
    assert aid is not None

    recent = attempt.get_recent(sid, limit=10)
    assert len(recent) == 1
    assert recent[0]['is_correct'] == 1


def test_end_session():
    sid = student.create("Alice")
    tid = topic.create("Math")
    nid = curriculum_node.create(tid, "Algebra")
    sess_id = session.create(sid)
    qid = question.create(nid, "Q1", "mcq", None, "A")
    attempt.create(qid, sid, sess_id, "A", 1)
    attempt.create(qid, sid, sess_id, "B", 0)

    session.end_session(sess_id)
    sess = session.get_by_id(sess_id)
    assert sess['total_questions'] == 2
    assert sess['total_correct'] == 1
