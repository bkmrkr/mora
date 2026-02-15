"""Tests for models/question_report.py — question quality reports."""
from models import question_report
from models import question as question_model
from models import curriculum_node as node_model
from models import topic as topic_model
from models import student as student_model


def _setup_question(topic_name='Math', node_name='Addition'):
    """Helper: create topic, node, and question, return question_id."""
    topic_id = topic_model.create(topic_name, 'test')
    node_id = node_model.create(topic_id, node_name, 'test node')
    qid = question_model.create(
        curriculum_node_id=node_id,
        content='What is 2+2?',
        question_type='mcq',
        options='["2","3","4","5"]',
        correct_answer='4',
        difficulty=500,
    )
    return qid


def test_create_report():
    qid = _setup_question()
    sid = student_model.create('TestStudent')
    question_report.create(qid, student_id=sid, reason='wrong_answer', details='Answer shown is incorrect')
    reports = question_report.get_by_question(qid)
    assert len(reports) == 1
    assert reports[0]['reason'] == 'wrong_answer'
    assert reports[0]['details'] == 'Answer shown is incorrect'
    assert reports[0]['student_id'] == sid


def test_create_report_no_student():
    qid = _setup_question()
    question_report.create(qid, reason='confusing')
    reports = question_report.get_by_question(qid)
    assert len(reports) == 1
    assert reports[0]['student_id'] is None


def test_get_by_question_returns_empty_for_no_reports():
    qid = _setup_question()
    reports = question_report.get_by_question(qid)
    assert reports == []


def test_mark_as_rejected_sets_test_status():
    qid = _setup_question()
    question_report.mark_as_rejected(qid, reason='bad_question')
    q = question_model.get_by_id(qid)
    assert q['test_status'] == 'rejected'
    assert q['validation_error'] == 'bad_question'


def test_mark_as_rejected_hides_from_approved():
    """After rejection, get_by_id_approved should return None."""
    qid = _setup_question()
    question_report.mark_as_rejected(qid, reason='wrong')
    assert question_model.get_by_id_approved(qid) is None


def test_get_rejected_questions():
    qid1 = _setup_question('Math1', 'Node1')
    qid2 = _setup_question('Math2', 'Node2')
    question_report.mark_as_rejected(qid1, 'bad')
    rejected = question_report.get_rejected_questions()
    assert any(r['id'] == qid1 for r in rejected)
    assert not any(r['id'] == qid2 for r in rejected)
