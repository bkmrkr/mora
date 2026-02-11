"""Tests for DB persistence — sessions survive restarts, skill history tracked.

Test categories:
  1. Schema & migrations — new tables and columns exist
  2. Session state persistence — current_question_id, last_result_json
  3. Skill history — rating tracked over time
  4. Attempt snapshots — skill_rating_before/after per attempt
  5. Answer service integration — end-to-end persistence
  6. Session resume — load state from DB when flask_session is empty
"""
import json

from models import (
    student, topic, curriculum_node, question, attempt,
    student_skill, session,
)
from db.database import query_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_student_and_topic():
    """Create a student, topic, and curriculum node. Returns (student_id, topic_id, node_id)."""
    sid = student.create("TestKid")
    tid = topic.create("Math")
    nid = curriculum_node.create(tid, "Addition", "Adding numbers", 0)
    return sid, tid, nid


def _create_question(node_id, content="What is 2+2?", correct="4"):
    return question.create(
        curriculum_node_id=node_id,
        content=content,
        question_type='mcq',
        options=json.dumps(['A) 3', 'B) 4', 'C) 5', 'D) 6']),
        correct_answer=correct,
        difficulty=600,
        estimated_p_correct=0.8,
    )


# ===========================================================================
# 1. Schema & Migrations
# ===========================================================================

class TestSchema:
    """Verify new tables and columns exist after init_db()."""

    def test_skill_history_table_exists(self):
        rows = query_db("PRAGMA table_info(skill_history)")
        cols = {r['name'] for r in rows}
        assert 'skill_rating' in cols
        assert 'uncertainty' in cols
        assert 'mastery_level' in cols
        assert 'attempt_id' in cols
        assert 'student_id' in cols
        assert 'curriculum_node_id' in cols

    def test_sessions_has_current_question_id(self):
        rows = query_db("PRAGMA table_info(sessions)")
        cols = {r['name'] for r in rows}
        assert 'current_question_id' in cols

    def test_sessions_has_last_result_json(self):
        rows = query_db("PRAGMA table_info(sessions)")
        cols = {r['name'] for r in rows}
        assert 'last_result_json' in cols

    def test_attempts_has_skill_rating_before(self):
        rows = query_db("PRAGMA table_info(attempts)")
        cols = {r['name'] for r in rows}
        assert 'skill_rating_before' in cols

    def test_attempts_has_skill_rating_after(self):
        rows = query_db("PRAGMA table_info(attempts)")
        cols = {r['name'] for r in rows}
        assert 'skill_rating_after' in cols

    def test_attempts_has_curriculum_node_id(self):
        rows = query_db("PRAGMA table_info(attempts)")
        cols = {r['name'] for r in rows}
        assert 'curriculum_node_id' in cols

    def test_migration_is_idempotent(self):
        """Running init_db twice doesn't fail."""
        from db.database import init_db
        init_db()  # Already ran in fixture, run again
        rows = query_db("PRAGMA table_info(skill_history)")
        assert len(rows) > 0


# ===========================================================================
# 2. Session State Persistence
# ===========================================================================

class TestSessionState:
    """current_question_id and last_result_json persist to DB."""

    def test_update_current_question(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        session.update_current_question(sess_id, qid)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid

    def test_update_current_question_overwrites(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid1 = _create_question(nid, content="Q1")
        qid2 = _create_question(nid, content="Q2")

        session.update_current_question(sess_id, qid1)
        session.update_current_question(sess_id, qid2)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid2

    def test_update_last_result(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        result = {'is_correct': True, 'skill_rating': 812.5}
        session.update_last_result(sess_id, json.dumps(result))

        sess = session.get_by_id(sess_id)
        loaded = json.loads(sess['last_result_json'])
        assert loaded['is_correct'] is True
        assert loaded['skill_rating'] == 812.5

    def test_last_result_json_initially_null(self):
        sid, _, _ = _setup_student_and_topic()
        sess_id = session.create(sid)
        sess = session.get_by_id(sess_id)
        assert sess['last_result_json'] is None

    def test_current_question_id_initially_null(self):
        sid, _, _ = _setup_student_and_topic()
        sess_id = session.create(sid)
        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] is None


# ===========================================================================
# 3. Skill History
# ===========================================================================

class TestSkillHistory:
    """skill_history table tracks every rating change."""

    def test_record_history_creates_entry(self):
        sid, tid, nid = _setup_student_and_topic()
        student_skill.record_history(sid, nid, 850.0, 400.0, 0.5)
        hist = student_skill.get_history(sid)
        assert len(hist) == 1
        assert hist[0]['skill_rating'] == 850.0
        assert hist[0]['uncertainty'] == 400.0
        assert hist[0]['mastery_level'] == 0.5

    def test_history_grows_with_each_update(self):
        sid, tid, nid = _setup_student_and_topic()
        student_skill.record_history(sid, nid, 800.0, 500.0, 0.3)
        student_skill.record_history(sid, nid, 820.0, 450.0, 0.4)
        student_skill.record_history(sid, nid, 840.0, 405.0, 0.5)
        hist = student_skill.get_history(sid, nid)
        assert len(hist) == 3
        ratings = [h['skill_rating'] for h in hist]
        assert ratings == [800.0, 820.0, 840.0]

    def test_history_links_to_attempt(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        aid = attempt.create(qid, sid, sess_id, "4", 1)
        student_skill.record_history(sid, nid, 815.0, 450.0, 0.4, attempt_id=aid)

        hist = student_skill.get_history(sid)
        assert hist[0]['attempt_id'] == aid

    def test_history_filtered_by_node(self):
        sid = student.create("TestKid")
        tid = topic.create("Math")
        nid1 = curriculum_node.create(tid, "Addition")
        nid2 = curriculum_node.create(tid, "Subtraction")

        student_skill.record_history(sid, nid1, 800.0, 500.0, 0.3)
        student_skill.record_history(sid, nid2, 750.0, 500.0, 0.2)
        student_skill.record_history(sid, nid1, 820.0, 450.0, 0.4)

        hist_add = student_skill.get_history(sid, nid1)
        hist_sub = student_skill.get_history(sid, nid2)
        assert len(hist_add) == 2
        assert len(hist_sub) == 1

    def test_history_preserves_chronological_order(self):
        sid, tid, nid = _setup_student_and_topic()
        for rating in [800, 815, 830, 810, 825]:
            student_skill.record_history(sid, nid, float(rating), 400.0, 0.3)
        hist = student_skill.get_history(sid, nid)
        ratings = [h['skill_rating'] for h in hist]
        assert ratings == [800.0, 815.0, 830.0, 810.0, 825.0]

    def test_history_empty_for_new_student(self):
        hist = student_skill.get_history(9999)
        assert hist == []


# ===========================================================================
# 4. Attempt Snapshots
# ===========================================================================

class TestAttemptSnapshots:
    """attempts table stores skill_rating_before/after and curriculum_node_id."""

    def test_attempt_stores_skill_ratings(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        aid = attempt.create(
            qid, sid, sess_id, "4", 1,
            curriculum_node_id=nid,
            skill_rating_before=800.0,
            skill_rating_after=815.5,
        )
        recent = attempt.get_recent(sid, limit=1)
        assert recent[0]['skill_rating_before'] == 800.0
        assert recent[0]['skill_rating_after'] == 815.5

    def test_attempt_stores_curriculum_node_id(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        attempt.create(
            qid, sid, sess_id, "4", 1,
            curriculum_node_id=nid,
        )
        row = query_db(
            "SELECT curriculum_node_id FROM attempts ORDER BY id DESC LIMIT 1",
            one=True,
        )
        assert row['curriculum_node_id'] == nid

    def test_attempt_without_snapshots_is_null(self):
        """Old-style create (no snapshots) stores NULL — backward compatible."""
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        attempt.create(qid, sid, sess_id, "4", 1)
        row = query_db(
            "SELECT skill_rating_before, skill_rating_after FROM attempts ORDER BY id DESC LIMIT 1",
            one=True,
        )
        assert row['skill_rating_before'] is None
        assert row['skill_rating_after'] is None

    def test_rating_delta_computable(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        attempt.create(
            qid, sid, sess_id, "4", 1,
            skill_rating_before=800.0,
            skill_rating_after=812.8,
        )
        row = query_db(
            "SELECT skill_rating_after - skill_rating_before as delta FROM attempts ORDER BY id DESC LIMIT 1",
            one=True,
        )
        assert abs(row['delta'] - 12.8) < 0.01


# ===========================================================================
# 5. Answer Service Integration
# ===========================================================================

class TestAnswerServicePersistence:
    """process_answer() stores skill history and attempt snapshots."""

    def _setup_for_answer(self):
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)
        stud = student.get_by_id(sid)
        current_question = {
            'question_id': qid,
            'node_id': nid,
            'node_name': 'Addition',
            'content': 'What is 2+2?',
            'question_type': 'mcq',
            'options': ['A) 3', 'B) 4', 'C) 5', 'D) 6'],
            'correct_answer': 'B) 4',
            'difficulty': 600,
        }
        return stud, current_question, sess_id, nid

    def test_process_answer_creates_skill_history(self):
        from services.answer_service import process_answer
        stud, current_q, sess_id, nid = self._setup_for_answer()

        process_answer(stud, current_q, 'B', 3.0, sess_id)

        hist = student_skill.get_history(stud['id'], nid)
        assert len(hist) == 1
        assert hist[0]['skill_rating'] > 800.0  # correct answer → rating up

    def test_process_answer_stores_attempt_snapshots(self):
        from services.answer_service import process_answer
        stud, current_q, sess_id, nid = self._setup_for_answer()

        process_answer(stud, current_q, 'B', 3.0, sess_id)

        row = query_db(
            "SELECT skill_rating_before, skill_rating_after, curriculum_node_id "
            "FROM attempts ORDER BY id DESC LIMIT 1",
            one=True,
        )
        assert row['skill_rating_before'] == 800.0
        assert row['skill_rating_after'] > 800.0
        assert row['curriculum_node_id'] == nid

    def test_process_answer_wrong_decreases_rating(self):
        from services.answer_service import process_answer
        stud, current_q, sess_id, nid = self._setup_for_answer()

        process_answer(stud, current_q, 'A', 3.0, sess_id)  # wrong answer

        hist = student_skill.get_history(stud['id'], nid)
        assert hist[0]['skill_rating'] < 800.0

    def test_multiple_answers_grow_history(self):
        from services.answer_service import process_answer
        stud, current_q, sess_id, nid = self._setup_for_answer()

        # Answer 3 questions
        for ans in ['B', 'A', 'B']:
            qid = _create_question(nid, content=f"Q {ans}")
            current_q['question_id'] = qid
            process_answer(stud, current_q, ans, 2.0, sess_id)

        hist = student_skill.get_history(stud['id'], nid)
        assert len(hist) == 3

    def test_skill_history_links_to_attempt(self):
        from services.answer_service import process_answer
        stud, current_q, sess_id, nid = self._setup_for_answer()

        process_answer(stud, current_q, 'B', 3.0, sess_id)

        hist = student_skill.get_history(stud['id'], nid)
        assert hist[0]['attempt_id'] is not None
        # Verify the linked attempt exists
        att = query_db("SELECT id FROM attempts WHERE id=?",
                        (hist[0]['attempt_id'],), one=True)
        assert att is not None


# ===========================================================================
# 6. Question Load from DB
# ===========================================================================

class TestQuestionLoadFromDB:
    """_load_question_from_db reconstructs question_dict from DB."""

    def test_load_question_from_db(self):
        from routes.session import _load_question_from_db
        sid, tid, nid = _setup_student_and_topic()
        qid = _create_question(nid, content="What is 3+5?", correct="8")

        q = _load_question_from_db(qid)
        assert q is not None
        assert q['question_id'] == qid
        assert q['content'] == "What is 3+5?"
        assert q['correct_answer'] == "8"
        assert q['node_id'] == nid
        assert q['node_name'] == "Addition"
        assert q['question_type'] == 'mcq'
        assert q['difficulty'] == 600

    def test_load_nonexistent_question_returns_none(self):
        from routes.session import _load_question_from_db
        assert _load_question_from_db(99999) is None

    def test_load_question_has_options(self):
        from routes.session import _load_question_from_db
        _, _, nid = _setup_student_and_topic()
        qid = _create_question(nid)
        q = _load_question_from_db(qid)
        assert q['options'] is not None
        assert len(q['options']) == 4

    def test_load_question_has_difficulty_score(self):
        from routes.session import _load_question_from_db
        _, _, nid = _setup_student_and_topic()
        qid = _create_question(nid)
        q = _load_question_from_db(qid)
        assert 'difficulty_score' in q
        assert 1 <= q['difficulty_score'] <= 10


# ===========================================================================
# 7. End-to-End: Session Resume After Restart
# ===========================================================================

class TestSessionResume:
    """Simulate restart: clear flask_session, verify DB-based resume."""

    def test_session_has_question_after_generation(self, app):
        """After generate_next, session DB has current_question_id."""
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        stud = student.get_by_id(sid)

        with app.app_context():
            # We can't easily call generate_next (needs LLM), but we can
            # verify the model layer works
            qid = _create_question(nid)
            session.update_current_question(sess_id, qid)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid

    def test_resume_loads_question_from_db(self, app):
        """Question route loads from DB when flask_session is empty."""
        from routes.session import _load_question_from_db
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid, content="Resumed question")
        session.update_current_question(sess_id, qid)

        # Simulate restart: no flask_session, but DB has the question
        sess = session.get_by_id(sess_id)
        q = _load_question_from_db(sess['current_question_id'])
        assert q is not None
        assert q['content'] == "Resumed question"

    def test_resume_loads_last_result_from_db(self):
        """Feedback route loads last_result from DB when flask_session is empty."""
        sid, _, _ = _setup_student_and_topic()
        sess_id = session.create(sid)
        result = {
            'is_correct': False,
            'skill_rating': 785.3,
            'student_answer': 'A',
            'correct_answer': 'B) 4',
        }
        session.update_last_result(sess_id, json.dumps(result))

        # Simulate restart: load from DB
        sess = session.get_by_id(sess_id)
        loaded = json.loads(sess['last_result_json'])
        assert loaded['is_correct'] is False
        assert loaded['skill_rating'] == 785.3
        assert loaded['student_answer'] == 'A'

    def test_end_session_still_works(self):
        """end_session computes totals correctly with new columns present."""
        sid, tid, nid = _setup_student_and_topic()
        sess_id = session.create(sid, tid)
        qid = _create_question(nid)

        attempt.create(qid, sid, sess_id, "B", 1,
                        curriculum_node_id=nid, skill_rating_before=800.0,
                        skill_rating_after=812.0)
        attempt.create(qid, sid, sess_id, "A", 0,
                        curriculum_node_id=nid, skill_rating_before=812.0,
                        skill_rating_after=790.0)

        session.end_session(sess_id)
        sess = session.get_by_id(sess_id)
        assert sess['total_questions'] == 2
        assert sess['total_correct'] == 1
        assert sess['ended_at'] is not None
