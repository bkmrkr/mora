"""Tests for all v2 model CRUD operations."""
import json

from models import student, session, question, attempt
from models.progress import get, upsert, get_for_student


# ── Student ──────────────────────────────────────────────────

class TestStudent:
    def test_create_and_get(self):
        sid = student.create('Alice')
        assert sid is not None
        row = student.get_by_id(sid)
        assert row['name'] == 'Alice'

    def test_get_by_name(self):
        student.create('Bob')
        row = student.get_by_name('Bob')
        assert row is not None
        assert row['name'] == 'Bob'

    def test_get_by_name_case_insensitive(self):
        student.create('Charlie')
        assert student.get_by_name('charlie') is not None
        assert student.get_by_name('CHARLIE') is not None
        assert student.get_by_name('Charlie')['name'] == 'Charlie'

    def test_get_by_name_missing(self):
        assert student.get_by_name('Nobody') is None

    def test_get_all(self):
        student.create('Zara')
        student.create('Amy')
        rows = student.get_all()
        names = [r['name'] for r in rows]
        assert 'Amy' in names
        assert 'Zara' in names
        # Sorted by name
        assert names.index('Amy') < names.index('Zara')

    def test_unique_name(self):
        student.create('Unique')
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            student.create('Unique')


# ── Progress ─────────────────────────────────────────────────

class TestProgress:
    def test_defaults_when_missing(self):
        sid = student.create('Test')
        prog = get(sid, 'g1_add_10')
        assert prog['skill_rating'] == 800.0
        assert prog['uncertainty'] == 350.0
        assert prog['mastery_level'] == 0.0
        assert prog['total_attempts'] == 0

    def test_upsert_creates(self):
        sid = student.create('Test')
        upsert(sid, 'g1_add_10', 850.0, 300.0, 0.3, 5, 4)
        prog = get(sid, 'g1_add_10')
        assert prog['skill_rating'] == 850.0
        assert prog['total_attempts'] == 5
        assert prog['correct_attempts'] == 4

    def test_upsert_updates(self):
        sid = student.create('Test')
        upsert(sid, 'g1_add_10', 850.0, 300.0, 0.3, 5, 4)
        upsert(sid, 'g1_add_10', 900.0, 250.0, 0.5, 10, 8)
        prog = get(sid, 'g1_add_10')
        assert prog['skill_rating'] == 900.0
        assert prog['total_attempts'] == 10

    def test_get_for_student(self):
        sid = student.create('Test')
        upsert(sid, 'g1_add_10', 850.0, 300.0, 0.3, 5, 4)
        upsert(sid, 'g1_sub_10', 800.0, 350.0, 0.0, 0, 0)
        rows = get_for_student(sid)
        assert len(rows) == 2
        skill_ids = [r['skill_id'] for r in rows]
        assert 'g1_add_10' in skill_ids
        assert 'g1_sub_10' in skill_ids


# ── Session ──────────────────────────────────────────────────

class TestSession:
    def test_create_and_get(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        assert sess_id is not None
        row = session.get_by_id(sess_id)
        assert row['student_id'] == sid
        assert row['ended_at'] is None

    def test_end_session(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        # Create a question and attempt first
        qid = question.create('g1_add_10', 'What is 2+3?', 'mcq',
                              json.dumps(['3', '4', '5', '6']), '5',
                              explanation='2+3=5', difficulty=600.0,
                              template_id='g1_add_10_basic')
        attempt.create(qid, sid, sess_id, 'g1_add_10', '5', 1)
        session.end_session(sess_id)
        row = session.get_by_id(sess_id)
        assert row['ended_at'] is not None
        assert row['total_questions'] == 1
        assert row['total_correct'] == 1

    def test_update_current_question(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        qid = question.create('g1_add_10', 'What is 1+1?', 'mcq',
                              json.dumps(['1', '2', '3', '4']), '2')
        session.update_current_question(sess_id, qid)
        row = session.get_by_id(sess_id)
        assert row['current_question_id'] == qid

    def test_update_last_result(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        result = json.dumps({'correct': True})
        session.update_last_result(sess_id, result)
        row = session.get_by_id(sess_id)
        assert json.loads(row['last_result_json'])['correct'] is True

    def test_get_for_student(self):
        sid = student.create('Test')
        session.create(sid)
        session.create(sid)
        rows = session.get_for_student(sid)
        assert len(rows) == 2


# ── Question ─────────────────────────────────────────────────

class TestQuestion:
    def test_create_and_get(self):
        qid = question.create(
            'g1_add_10', 'What is 3+4?', 'mcq',
            json.dumps(['5', '6', '7', '8']), '7',
            explanation='3+4=7', difficulty=650.0,
            template_id='g1_add_10_basic',
        )
        row = question.get_by_id(qid)
        assert row['skill_id'] == 'g1_add_10'
        assert row['content'] == 'What is 3+4?'
        assert row['correct_answer'] == '7'
        assert row['template_id'] == 'g1_add_10_basic'
        opts = json.loads(row['options'])
        assert '7' in opts
        assert len(opts) == 4

    def test_get_for_skill(self):
        question.create('g1_add_10', 'Q1', 'mcq', '[]', '1')
        question.create('g1_add_10', 'Q2', 'mcq', '[]', '2')
        question.create('g1_sub_10', 'Q3', 'mcq', '[]', '3')
        rows = question.get_for_skill('g1_add_10')
        assert len(rows) == 2
        assert all(r['skill_id'] == 'g1_add_10' for r in rows)


# ── Attempt ──────────────────────────────────────────────────

class TestAttempt:
    def _setup(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        qid = question.create('g1_add_10', 'What is 1+2?', 'mcq',
                              json.dumps(['1', '2', '3', '4']), '3')
        return sid, sess_id, qid

    def test_create_and_count(self):
        sid, sess_id, qid = self._setup()
        attempt.create(qid, sid, sess_id, 'g1_add_10', '3', 1,
                       skill_rating_before=800.0, skill_rating_after=810.0)
        assert attempt.count_for_student(sid) == 1

    def test_get_recent(self):
        sid, sess_id, qid = self._setup()
        attempt.create(qid, sid, sess_id, 'g1_add_10', '3', 1)
        attempt.create(qid, sid, sess_id, 'g1_add_10', '2', 0)
        rows = attempt.get_recent(sid)
        assert len(rows) == 2
        answers = {r['answer_given'] for r in rows}
        assert answers == {'3', '2'}

    def test_get_recent_for_skill(self):
        sid, sess_id, qid = self._setup()
        qid2 = question.create('g1_sub_10', 'What is 5-3?', 'mcq',
                               json.dumps(['1', '2', '3', '4']), '2')
        attempt.create(qid, sid, sess_id, 'g1_add_10', '3', 1)
        attempt.create(qid2, sid, sess_id, 'g1_sub_10', '2', 1)
        rows = attempt.get_recent_for_skill(sid, 'g1_add_10')
        assert len(rows) == 1

    def test_get_for_session(self):
        sid, sess_id, qid = self._setup()
        attempt.create(qid, sid, sess_id, 'g1_add_10', '3', 1)
        rows = attempt.get_for_session(sess_id)
        assert len(rows) == 1
        assert rows[0]['content'] == 'What is 1+2?'


import pytest
