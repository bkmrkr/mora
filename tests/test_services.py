"""Tests for question_service and answer_service — full generate→answer→update cycle."""
from models import student, session
from models.progress import get as get_progress
from services import question_service, answer_service


class TestQuestionService:
    def test_generate_first_question(self):
        """First question for a new student should succeed."""
        sid = student.create('Test')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)

        q = question_service.generate_next(sess_id, s)
        assert q is not None
        assert 'question_id' in q
        assert 'content' in q
        assert 'options' in q
        assert 'correct_answer' in q
        assert 'skill_id' in q
        assert q['skill_id'].startswith('g1_')  # Should be grade 1

    def test_generate_stores_in_db(self):
        """Generated question should be stored in the questions table."""
        sid = student.create('Test')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)

        q = question_service.generate_next(sess_id, s)
        from models import question
        row = question.get_by_id(q['question_id'])
        assert row is not None
        assert row['content'] == q['content']

    def test_generate_updates_session(self):
        """Session should track current question."""
        sid = student.create('Test')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)

        q = question_service.generate_next(sess_id, s)
        sess = session.get_by_id(sess_id)
        assert sess['current_question_id'] == q['question_id']

    def test_variety_not_same_skill(self):
        """Second question should pick a different skill."""
        sid = student.create('Test')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)

        q1 = question_service.generate_next(sess_id, s)
        q2 = question_service.generate_next(sess_id, s, current_skill_id=q1['skill_id'])
        assert q2['skill_id'] != q1['skill_id']


class TestAnswerService:
    def _setup_question(self):
        sid = student.create('Test')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)
        q = question_service.generate_next(sess_id, s)
        return s, sess_id, q

    def test_correct_answer(self):
        s, sess_id, q = self._setup_question()
        result = answer_service.process_answer(
            s, q, q['correct_answer'], 2.0, sess_id
        )
        assert result['is_correct'] is True
        assert result['skill_rating'] > 800.0  # should increase

    def test_wrong_answer(self):
        s, sess_id, q = self._setup_question()
        # Pick a wrong answer
        wrong = [o for o in q['options'] if o != q['correct_answer']][0]
        result = answer_service.process_answer(
            s, q, wrong, 3.0, sess_id
        )
        assert result['is_correct'] is False

    def test_updates_progress(self):
        s, sess_id, q = self._setup_question()
        answer_service.process_answer(
            s, q, q['correct_answer'], 2.0, sess_id
        )
        prog = get_progress(s['id'], q['skill_id'])
        assert prog['total_attempts'] == 1
        assert prog['correct_attempts'] == 1
        assert prog['skill_rating'] > 800.0

    def test_records_attempt(self):
        s, sess_id, q = self._setup_question()
        answer_service.process_answer(
            s, q, q['correct_answer'], 2.0, sess_id
        )
        from models import attempt
        attempts = attempt.get_for_session(sess_id)
        assert len(attempts) == 1
        assert attempts[0]['is_correct'] == 1

    def test_full_cycle(self):
        """Generate → answer → generate → answer: ELO should move."""
        sid = student.create('Cycle')
        sess_id = session.create(sid)
        s = student.get_by_id(sid)

        # Question 1: correct
        q1 = question_service.generate_next(sess_id, s)
        r1 = answer_service.process_answer(s, q1, q1['correct_answer'], 1.0, sess_id)
        assert r1['is_correct']

        # Question 2: wrong
        q2 = question_service.generate_next(sess_id, s, current_skill_id=q1['skill_id'])
        wrong = [o for o in q2['options'] if o != q2['correct_answer']][0]
        r2 = answer_service.process_answer(s, q2, wrong, 2.0, sess_id)
        assert not r2['is_correct']

        # Both skills should have progress
        prog1 = get_progress(sid, q1['skill_id'])
        prog2 = get_progress(sid, q2['skill_id'])
        assert prog1['total_attempts'] == 1
        assert prog2['total_attempts'] == 1
