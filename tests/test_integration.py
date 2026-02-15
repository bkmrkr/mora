"""Full integration test — end-to-end student journey via Flask test client.

Tests the complete flow: home → start → answer questions → feedback → end → dashboard.
Verifies ELO updates, skill progression, and grade navigation.
"""
import json
import pytest


class TestFullStudentJourney:
    """20-question session with correct and wrong answers."""

    def _start_session(self, client, name='IntegrationKid'):
        resp = client.post('/start', data={'student_name': name},
                           follow_redirects=False)
        location = resp.headers['Location']
        session_id = location.split('/session/')[1].split('/')[0]
        return session_id

    def _get_current_question(self, client, session_id):
        """Load question page, return question data from session cookie."""
        client.get(f'/session/{session_id}/question')
        with client.session_transaction() as sess:
            return sess.get('current_question', {})

    def _answer_correctly(self, client, session_id, q):
        return client.post(f'/session/{session_id}/answer', data={
            'answer': q['correct_answer'],
            'question_id': q.get('question_id', ''),
            'response_time_s': '1.5',
        }, follow_redirects=False)

    def _answer_wrong(self, client, session_id, q):
        wrong = [o for o in q.get('options', []) if o != q['correct_answer']]
        answer = wrong[0] if wrong else 'definitely_wrong_answer'
        return client.post(f'/session/{session_id}/answer', data={
            'answer': answer,
            'question_id': q.get('question_id', ''),
            'response_time_s': '2.0',
        }, follow_redirects=False)

    def test_20_question_journey(self, client):
        """Answer 20 questions (15 correct, 5 wrong), verify full lifecycle."""
        from models import student as student_model
        from models import attempt as attempt_model
        from models.progress import get_for_student

        # 1. Start session
        session_id = self._start_session(client)

        answered = 0
        correct_count = 0
        wrong_count = 0
        skill_ids_seen = set()

        for i in range(20):
            q = self._get_current_question(client, session_id)
            assert q, f'No question generated on iteration {i}'
            assert 'correct_answer' in q
            assert 'question_id' in q
            skill_ids_seen.add(q['skill_id'])

            # Alternate: 3 correct, 1 wrong pattern
            if i % 4 == 3:
                resp = self._answer_wrong(client, session_id, q)
                wrong_count += 1
                assert '/feedback' in resp.headers['Location']
                # Load feedback and verify it shows explanation
                fb = client.get(f'/session/{session_id}/feedback')
                assert fb.status_code == 200
                assert b'Not quite' in fb.data
                # Click Next Question
                client.post(f'/session/{session_id}/next')
            else:
                resp = self._answer_correctly(client, session_id, q)
                correct_count += 1
                assert '/question' in resp.headers['Location']

            answered += 1

        assert answered == 20
        assert correct_count == 15
        assert wrong_count == 5

        # 2. End session
        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'Session Complete' in resp.data
        assert b'IntegrationKid' in resp.data

        # 3. Verify attempt records
        student = student_model.get_by_name('IntegrationKid')
        attempts = attempt_model.get_for_session(session_id)
        assert len(attempts) == 20
        actual_correct = sum(1 for a in attempts if a['is_correct'])
        assert actual_correct == 15

        # 4. Verify skill progress was updated
        progress = get_for_student(student['id'])
        assert len(progress) > 0, 'No progress records created'
        for p in progress:
            assert p['total_attempts'] > 0
            # Ratings should have changed from the default 800
            assert p['skill_rating'] != 800.0, \
                f'{p["skill_id"]}: rating unchanged from default'

        # 5. Verify dashboard shows progress
        resp = client.get(f'/dashboard/{student["id"]}')
        assert resp.status_code == 200
        assert b'IntegrationKid' in resp.data
        assert b'Grade 1' in resp.data

        # 6. Verify variety — should have practiced multiple skills
        assert len(skill_ids_seen) >= 2, \
            f'Only practiced {skill_ids_seen}, expected variety'

    def test_new_student_starts_at_grade1(self, client):
        """New student only sees grade 1 skills."""
        session_id = self._start_session(client, 'Newbie')
        q = self._get_current_question(client, session_id)
        assert q['skill_id'].startswith('g1_'), \
            f'New student got non-grade-1 skill: {q["skill_id"]}'

    def test_student_persistence_across_sessions(self, client):
        """Student progress persists across multiple sessions."""
        from models.progress import get_for_student
        from models import student as student_model

        # Session 1: answer 5 questions correctly
        sid1 = self._start_session(client, 'PersistKid')
        for _ in range(5):
            q = self._get_current_question(client, sid1)
            self._answer_correctly(client, sid1, q)
        client.get(f'/session/{sid1}/end')

        student = student_model.get_by_name('PersistKid')
        progress_after_s1 = get_for_student(student['id'])
        ratings_s1 = {p['skill_id']: p['skill_rating'] for p in progress_after_s1}

        # Session 2: answer 5 more questions correctly
        sid2 = self._start_session(client, 'PersistKid')
        for _ in range(5):
            q = self._get_current_question(client, sid2)
            self._answer_correctly(client, sid2, q)
        client.get(f'/session/{sid2}/end')

        progress_after_s2 = get_for_student(student['id'])
        ratings_s2 = {p['skill_id']: p['skill_rating'] for p in progress_after_s2}

        # Progress should have increased
        total_attempts_s2 = sum(p['total_attempts'] for p in progress_after_s2)
        assert total_attempts_s2 == 10, f'Expected 10 total attempts, got {total_attempts_s2}'

    def test_correct_skips_feedback_wrong_shows_it(self, client):
        """Correct answers skip feedback; wrong answers show it."""
        session_id = self._start_session(client, 'FlowKid')

        # Correct answer → redirect to /question (no feedback)
        q = self._get_current_question(client, session_id)
        resp = self._answer_correctly(client, session_id, q)
        assert '/question' in resp.headers['Location']
        assert '/feedback' not in resp.headers['Location']

        # Wrong answer → redirect to /feedback
        q = self._get_current_question(client, session_id)
        resp = self._answer_wrong(client, session_id, q)
        assert '/feedback' in resp.headers['Location']

    def test_dashboard_shows_all_grades(self, client):
        """Dashboard overview shows grades 1-4 for any student."""
        from models import student as student_model
        sid = student_model.create('DashTest')
        resp = client.get(f'/dashboard/{sid}')
        assert resp.status_code == 200
        assert b'Grade 1' in resp.data
        assert b'Grade 2' in resp.data
        assert b'Grade 3' in resp.data
        assert b'Grade 4' in resp.data

    def test_returning_student_chip(self, client):
        """After creating a student, home page shows their chip."""
        self._start_session(client, 'ChipKid')
        resp = client.get('/')
        assert b'ChipKid' in resp.data
        assert b'Returning students' in resp.data

    def test_session_summary_accuracy(self, client):
        """Summary page shows correct accuracy percentage."""
        session_id = self._start_session(client, 'AccuracyKid')

        # 3 correct, 1 wrong = 75%
        for i in range(4):
            q = self._get_current_question(client, session_id)
            if i < 3:
                self._answer_correctly(client, session_id, q)
            else:
                self._answer_wrong(client, session_id, q)
                client.post(f'/session/{session_id}/next')

        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'75%' in resp.data

    def test_empty_session_end(self, client):
        """Ending a session with no answers shows 0%."""
        session_id = self._start_session(client, 'EmptyKid')
        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'Session Complete' in resp.data


class TestAllTemplatesViable:
    """Ensure every skill's templates can be used in a real session."""

    def test_all_40_skills_registered(self):
        from services.question_service import TEMPLATES
        from curriculum.skills import get_all_skill_ids
        all_ids = set(get_all_skill_ids())
        registered = set(TEMPLATES.keys())
        missing = all_ids - registered
        assert not missing, f'Skills without templates: {missing}'
        extra = registered - all_ids
        assert not extra, f'Templates for non-existent skills: {extra}'

    def test_every_template_produces_valid_question(self):
        """Every registered template produces a question with required fields."""
        from services.question_service import TEMPLATES
        required = {'skill_id', 'question', 'correct_answer', 'options'}
        for skill_id, fns in TEMPLATES.items():
            for fn in fns:
                result = fn(800)
                missing = required - set(result.keys())
                assert not missing, f'{skill_id}: missing {missing}'
                assert len(result['options']) == 4
                assert len(set(result['options'])) == 4
                assert result['correct_answer'] in result['options']
