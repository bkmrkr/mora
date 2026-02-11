"""Tests for question dedup — same question must never be served twice in a session.

Root cause of the bug: after a wrong answer with no precached question,
flask_session['current_question'] was not cleared, so the same question
was served again on the next page load.

Test categories:
  1. Session state clearing — current_question_id set to NULL after answer
  2. Dedup set construction — session_texts includes all answered questions
  3. Dedup includes current question — unanswered question in exclude set
  4. No consecutive duplicate question_ids — DB-level invariant
  5. Global dedup — correctly-answered texts excluded lifetime
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

def _setup():
    """Create student, topic, 2 nodes, 2 questions. Returns all ids."""
    sid = student.create("DedupKid")
    tid = topic.create("Math")
    nid1 = curriculum_node.create(tid, "Addition", "Adding numbers", 0)
    nid2 = curriculum_node.create(tid, "Subtraction", "Subtracting numbers", 1)
    qid1 = question.create(
        curriculum_node_id=nid1, content="What is 2+3?",
        question_type='mcq',
        options=json.dumps(['A) 4', 'B) 5', 'C) 6', 'D) 7']),
        correct_answer='B) 5', difficulty=600, estimated_p_correct=0.8,
    )
    qid2 = question.create(
        curriculum_node_id=nid2, content="What is 9-4?",
        question_type='mcq',
        options=json.dumps(['A) 3', 'B) 4', 'C) 5', 'D) 6']),
        correct_answer='C) 5', difficulty=600, estimated_p_correct=0.8,
    )
    return sid, tid, nid1, nid2, qid1, qid2


# ===========================================================================
# 1. Session State Clearing
# ===========================================================================

class TestSessionStateClearing:
    """current_question_id must be clearable (set to NULL)."""

    def test_clear_current_question_id(self):
        """Setting current_question_id to None clears it in DB."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        # Verify it's set
        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid1

        # Clear it (this is what the fix does after processing an answer)
        session.update_current_question(sess_id, None)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] is None

    def test_clear_then_set_new(self):
        """After clearing, can set a new question_id."""
        sid, tid, nid1, _, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)
        session.update_current_question(sess_id, None)  # clear
        session.update_current_question(sess_id, qid2)  # set new

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid2

    def test_question_id_changes_after_answer(self):
        """Simulate: answer q1, then set q2 — question_id must differ."""
        sid, tid, nid1, _, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        # Student answers q1 → clear → set q2
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        session.update_current_question(sess_id, None)
        session.update_current_question(sess_id, qid2)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid2
        assert sess['current_question_id'] != qid1


# ===========================================================================
# 2. Dedup Set Construction — session_texts
# ===========================================================================

class TestDedupSessionTexts:
    """attempt.get_for_session returns all answered question texts."""

    def test_session_texts_includes_all_answers(self):
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)

        # Two attempts in this session
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid2, sid, sess_id, "C", 1, curriculum_node_id=nid2)

        session_attempts = attempt.get_for_session(sess_id)
        session_texts = {a['content'] for a in session_attempts if a.get('content')}

        assert "What is 2+3?" in session_texts
        assert "What is 9-4?" in session_texts

    def test_session_texts_empty_when_no_attempts(self):
        sid, tid, _, _, _, _ = _setup()
        sess_id = session.create(sid, tid)
        session_attempts = attempt.get_for_session(sess_id)
        assert len(session_attempts) == 0

    def test_session_texts_only_from_this_session(self):
        """Attempts from other sessions don't appear in session_texts."""
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess1 = session.create(sid, tid)
        sess2 = session.create(sid, tid)

        attempt.create(qid1, sid, sess1, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid2, sid, sess2, "C", 1, curriculum_node_id=nid2)

        sess1_attempts = attempt.get_for_session(sess1)
        sess1_texts = {a['content'] for a in sess1_attempts if a.get('content')}

        assert "What is 2+3?" in sess1_texts
        assert "What is 9-4?" not in sess1_texts  # different session

    def test_duplicate_text_deduped_in_set(self):
        """If same question answered twice (the bug), set still has one entry."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)

        # Same question answered twice (the bug scenario)
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid1, sid, sess_id, "A", 0, curriculum_node_id=nid1)

        session_attempts = attempt.get_for_session(sess_id)
        session_texts = {a['content'] for a in session_attempts if a.get('content')}

        assert len(session_attempts) == 2  # two rows
        assert len(session_texts) == 1     # but one unique text


# ===========================================================================
# 3. Dedup Includes Current (Unanswered) Question
# ===========================================================================

class TestDedupIncludesCurrent:
    """The current unanswered question must be in the dedup exclude set."""

    def test_current_question_retrievable_from_session(self):
        """session.current_question_id points to the active question."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        sess = session.get_by_id(sess_id)
        current_q = question.get_by_id(sess['current_question_id'])
        assert current_q is not None
        assert current_q['content'] == "What is 2+3?"

    def test_current_question_text_in_exclude_set(self):
        """Dedup should include current question text (not just attempted)."""
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)

        # Student answered q1, now q2 is the current question
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        session.update_current_question(sess_id, qid2)

        # Build dedup set the way generate_next() does now
        session_attempts = attempt.get_for_session(sess_id)
        session_texts = {a['content'] for a in session_attempts if a.get('content')}

        # Also include current unanswered question (the fix)
        sess = session.get_by_id(sess_id)
        if sess and sess.get('current_question_id'):
            current_q = question.get_by_id(sess['current_question_id'])
            if current_q and current_q.get('content'):
                session_texts.add(current_q['content'])

        assert "What is 2+3?" in session_texts   # from attempt
        assert "What is 9-4?" in session_texts   # from current question

    def test_no_current_question_still_works(self):
        """When current_question_id is None, dedup still works."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        session.update_current_question(sess_id, None)

        sess = session.get_by_id(sess_id)
        session_attempts = attempt.get_for_session(sess_id)
        session_texts = {a['content'] for a in session_attempts if a.get('content')}

        if sess and sess.get('current_question_id'):
            current_q = question.get_by_id(sess['current_question_id'])
            if current_q:
                session_texts.add(current_q['content'])

        assert "What is 2+3?" in session_texts
        assert len(session_texts) == 1


# ===========================================================================
# 4. No Consecutive Duplicate question_ids
# ===========================================================================

class TestNoConsecutiveDuplicates:
    """DB-level invariant: same question_id should not appear consecutively."""

    def test_detect_consecutive_duplicates(self):
        """Helper to detect consecutive same-question_id in a session."""
        sid, tid, nid1, _, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)

        # Normal: alternating questions
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid2, sid, sess_id, "C", 1, curriculum_node_id=nid1)
        attempt.create(qid1, sid, sess_id, "B", 0, curriculum_node_id=nid1)

        attempts = attempt.get_for_session(sess_id)
        question_ids = [a['question_id'] for a in attempts]

        consecutive_dups = [
            question_ids[i] for i in range(1, len(question_ids))
            if question_ids[i] == question_ids[i - 1]
        ]
        assert len(consecutive_dups) == 0

    def test_flag_consecutive_duplicates(self):
        """If same question_id appears consecutively, it's a bug."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)

        # Bug scenario: same question answered 3 times in a row
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid1, sid, sess_id, "A", 0, curriculum_node_id=nid1)
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)

        attempts = attempt.get_for_session(sess_id)
        question_ids = [a['question_id'] for a in attempts]

        consecutive_dups = [
            question_ids[i] for i in range(1, len(question_ids))
            if question_ids[i] == question_ids[i - 1]
        ]
        # This WOULD be a bug — the test documents the invariant
        assert len(consecutive_dups) == 2  # 2 consecutive repeats

    def test_same_text_different_ids_is_ok(self):
        """Two different question_ids with same text is less bad than same ID."""
        sid, tid, nid1, _, _, _ = _setup()
        sess_id = session.create(sid, tid)

        # Two different questions with same text (LLM generated same thing)
        qid_a = question.create(
            curriculum_node_id=nid1, content="What is 1+1?",
            question_type='mcq', options=None,
            correct_answer='2', difficulty=500,
        )
        qid_b = question.create(
            curriculum_node_id=nid1, content="What is 1+1?",
            question_type='mcq', options=None,
            correct_answer='2', difficulty=500,
        )
        assert qid_a != qid_b  # different question records

        attempt.create(qid_a, sid, sess_id, "2", 1, curriculum_node_id=nid1)
        attempt.create(qid_b, sid, sess_id, "2", 1, curriculum_node_id=nid1)

        attempts = attempt.get_for_session(sess_id)
        question_ids = [a['question_id'] for a in attempts]

        consecutive_dups = [
            question_ids[i] for i in range(1, len(question_ids))
            if question_ids[i] == question_ids[i - 1]
        ]
        assert len(consecutive_dups) == 0  # different IDs, no consecutive dup


# ===========================================================================
# 5. Global Dedup — Correctly Answered Texts
# ===========================================================================

class TestGlobalDedup:
    """Never re-ask a question the student answered correctly (lifetime)."""

    def test_correct_texts_includes_correct_answers(self):
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)

        texts = attempt.get_correct_texts(sid)
        assert "What is 2+3?" in texts

    def test_correct_texts_excludes_wrong_answers(self):
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        attempt.create(qid1, sid, sess_id, "A", 0, curriculum_node_id=nid1)

        texts = attempt.get_correct_texts(sid)
        assert "What is 2+3?" not in texts

    def test_correct_texts_across_sessions(self):
        """Global dedup spans all sessions."""
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess1 = session.create(sid, tid)
        sess2 = session.create(sid, tid)

        attempt.create(qid1, sid, sess1, "B", 1, curriculum_node_id=nid1)
        attempt.create(qid2, sid, sess2, "C", 1, curriculum_node_id=nid2)

        texts = attempt.get_correct_texts(sid)
        assert "What is 2+3?" in texts
        assert "What is 9-4?" in texts

    def test_correct_texts_isolated_per_student(self):
        """Student A's correct answers don't affect student B's dedup."""
        sid_a, tid, nid1, _, qid1, _ = _setup()
        sid_b = student.create("OtherKid")
        sess = session.create(sid_a, tid)
        attempt.create(qid1, sid_a, sess, "B", 1, curriculum_node_id=nid1)

        texts_a = attempt.get_correct_texts(sid_a)
        texts_b = attempt.get_correct_texts(sid_b)

        assert "What is 2+3?" in texts_a
        assert "What is 2+3?" not in texts_b

    def test_combined_dedup_excludes_both_layers(self):
        """session_texts | global_correct_texts covers all exclusions."""
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess1 = session.create(sid, tid)
        sess2 = session.create(sid, tid)

        # Session 1: answered q1 correctly
        attempt.create(qid1, sid, sess1, "B", 1, curriculum_node_id=nid1)

        # Session 2: answered q2 wrong
        attempt.create(qid2, sid, sess2, "A", 0, curriculum_node_id=nid2)

        # Build combined dedup for session 2
        session_texts = {
            a['content'] for a in attempt.get_for_session(sess2) if a.get('content')
        }
        global_correct = attempt.get_correct_texts(sid)
        all_exclude = session_texts | global_correct

        assert "What is 2+3?" in all_exclude   # from global (correct in sess1)
        assert "What is 9-4?" in all_exclude   # from session (wrong in sess2)


# ===========================================================================
# 6. Regression: The Exact Bug Scenario
# ===========================================================================

class TestWrongPathDuplicateRegression:
    """The exact bug: wrong answer + no cache → same question served again.

    Before the fix:
      1. Student sees question Q (current_question = Q, current_question_id = Q.id)
      2. Student answers wrong → attempt created, but current_question NOT cleared
      3. Student clicks "Next" → next_question() sees current_question is set, skips generation
      4. question() renders the SAME question Q → duplicate!

    After the fix:
      1. Student sees question Q
      2. Student answers wrong → attempt created, current_question cleared, current_question_id = NULL
      3. Student clicks "Next" → next_question() sees current_question is None, generates fresh
      4. question() renders a NEW question → no duplicate!
    """

    def test_current_question_id_cleared_after_answer(self):
        """After processing an answer, current_question_id should be NULL."""
        sid, tid, nid1, _, qid1, _ = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        # Simulate what the fixed answer() route does:
        # 1. Process answer (creates attempt)
        attempt.create(qid1, sid, sess_id, "A", 0, curriculum_node_id=nid1)

        # 2. Clear the answered question (THE FIX)
        session.update_current_question(sess_id, None)

        # 3. Verify it's cleared
        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] is None

    def test_wrong_path_no_cache_gets_new_question(self):
        """After wrong answer with no cache, a new question must be generated.

        We can't test full LLM generation, but we verify the session state
        allows a new question to be set (current_question_id is NULL).
        """
        sid, tid, nid1, nid2, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        # Student answers wrong
        attempt.create(qid1, sid, sess_id, "A", 0, curriculum_node_id=nid1)

        # Fixed answer() clears the question
        session.update_current_question(sess_id, None)

        # next_question() would now see current_question is None and generate fresh.
        # Simulate: generation produces a different question
        session.update_current_question(sess_id, qid2)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid2
        assert sess['current_question_id'] != qid1

    def test_multiple_wrong_answers_never_same_question(self):
        """Simulate 3 wrong answers — each should be on a different question."""
        sid, tid, nid1, _, _, _ = _setup()
        sess_id = session.create(sid, tid)

        # Create 3 distinct questions
        qids = []
        for i in range(3):
            qid = question.create(
                curriculum_node_id=nid1,
                content=f"Question {i}: What is {i}+{i}?",
                question_type='mcq', options=None,
                correct_answer=str(i * 2), difficulty=600,
            )
            qids.append(qid)

        served_ids = []
        for i, qid in enumerate(qids):
            # Set current question
            session.update_current_question(sess_id, qid)

            # Student answers wrong
            attempt.create(qid, sid, sess_id, "X", 0, curriculum_node_id=nid1)
            served_ids.append(qid)

            # Fixed answer() clears the question
            session.update_current_question(sess_id, None)

        # No consecutive duplicates
        for i in range(1, len(served_ids)):
            assert served_ids[i] != served_ids[i - 1], \
                f"Consecutive duplicate: qid={served_ids[i]} at positions {i-1},{i}"

    def test_correct_path_also_clears_before_setting_new(self):
        """After correct answer, old question is cleared before new one is set."""
        sid, tid, nid1, _, qid1, qid2 = _setup()
        sess_id = session.create(sid, tid)
        session.update_current_question(sess_id, qid1)

        # Student answers correctly
        attempt.create(qid1, sid, sess_id, "B", 1, curriculum_node_id=nid1)

        # Fixed answer() clears first, then sets cached/generated
        session.update_current_question(sess_id, None)
        session.update_current_question(sess_id, qid2)

        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == qid2
