"""Route tests — full HTTP flow for home, session, and dashboard."""
import json
import pytest


class TestHome:
    def test_index_page(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'Mora Math' in resp.data

    def test_index_shows_returning_students(self, client):
        from models import student as student_model
        student_model.create('Alice')
        resp = client.get('/')
        assert b'Alice' in resp.data
        assert b'Returning students' in resp.data

    def test_start_creates_student_and_session(self, client):
        resp = client.post('/start', data={'student_name': 'Bob'},
                           follow_redirects=False)
        assert resp.status_code == 302
        assert '/session/' in resp.headers['Location']

    def test_start_reuses_existing_student(self, client):
        from models import student as student_model
        student_model.create('Carol')
        resp = client.post('/start', data={'student_name': 'Carol'},
                           follow_redirects=False)
        assert resp.status_code == 302
        # Should still have only 1 student named Carol
        students = student_model.get_all()
        carol_count = sum(1 for s in students if s['name'] == 'Carol')
        assert carol_count == 1

    def test_start_empty_name_redirects(self, client):
        resp = client.post('/start', data={'student_name': ''},
                           follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/')


class TestSession:
    def _start_session(self, client):
        """Helper: create student, start session, return session_id."""
        resp = client.post('/start', data={'student_name': 'TestKid'},
                           follow_redirects=False)
        location = resp.headers['Location']
        # Location like /session/<uuid>/question
        session_id = location.split('/session/')[1].split('/')[0]
        return session_id

    def test_question_page_renders(self, client):
        session_id = self._start_session(client)
        resp = client.get(f'/session/{session_id}/question')
        assert resp.status_code == 200
        assert b'TestKid' in resp.data
        assert b'answer-form' in resp.data

    def test_question_shows_options(self, client):
        session_id = self._start_session(client)
        resp = client.get(f'/session/{session_id}/question')
        assert b'choice-btn' in resp.data

    def test_correct_answer_redirects_to_question(self, client):
        session_id = self._start_session(client)
        # Load question page to populate flask session
        client.get(f'/session/{session_id}/question')

        # Get the current question from the session cookie
        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            qid = q.get('question_id', '')

        resp = client.post(f'/session/{session_id}/answer', data={
            'answer': correct,
            'question_id': qid,
            'response_time_s': '1.5',
        }, follow_redirects=False)
        assert resp.status_code == 302
        # Correct answer should redirect back to question (skip feedback)
        assert '/question' in resp.headers['Location']

    def test_wrong_answer_shows_feedback(self, client):
        session_id = self._start_session(client)
        client.get(f'/session/{session_id}/question')

        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            options = q.get('options', [])
            qid = q.get('question_id', '')

        # Pick a wrong answer
        wrong = [o for o in options if o != correct]
        wrong_answer = wrong[0] if wrong else 'definitely_wrong'

        resp = client.post(f'/session/{session_id}/answer', data={
            'answer': wrong_answer,
            'question_id': qid,
            'response_time_s': '2.0',
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/feedback' in resp.headers['Location']

    def test_feedback_page_renders(self, client):
        session_id = self._start_session(client)
        client.get(f'/session/{session_id}/question')

        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            options = q.get('options', [])
            qid = q.get('question_id', '')

        wrong = [o for o in options if o != correct]
        wrong_answer = wrong[0] if wrong else 'wrong'

        client.post(f'/session/{session_id}/answer', data={
            'answer': wrong_answer,
            'question_id': qid,
            'response_time_s': '2.0',
        })
        resp = client.get(f'/session/{session_id}/feedback')
        assert resp.status_code == 200
        assert b'Not quite' in resp.data
        assert b'Correct answer' in resp.data

    def test_next_question_after_feedback(self, client):
        session_id = self._start_session(client)
        client.get(f'/session/{session_id}/question')

        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            options = q.get('options', [])
            qid = q.get('question_id', '')

        wrong = [o for o in options if o != correct]
        wrong_answer = wrong[0] if wrong else 'wrong'

        client.post(f'/session/{session_id}/answer', data={
            'answer': wrong_answer,
            'question_id': qid,
            'response_time_s': '2.0',
        })
        # Click "Next Question" from feedback page
        resp = client.post(f'/session/{session_id}/next',
                           follow_redirects=False)
        assert resp.status_code == 302
        assert '/question' in resp.headers['Location']

    def test_end_session_shows_summary(self, client):
        session_id = self._start_session(client)
        # Answer one question first
        client.get(f'/session/{session_id}/question')

        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            qid = q.get('question_id', '')

        client.post(f'/session/{session_id}/answer', data={
            'answer': correct,
            'question_id': qid,
            'response_time_s': '1.0',
        })

        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'Session Complete' in resp.data
        assert b'TestKid' in resp.data

    def test_end_session_zero_questions(self, client):
        session_id = self._start_session(client)
        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'Session Complete' in resp.data

    def test_invalid_session_redirects_home(self, client):
        resp = client.get('/session/nonexistent-id/question',
                          follow_redirects=False)
        assert resp.status_code == 302

    def test_empty_answer_redirects_back(self, client):
        session_id = self._start_session(client)
        client.get(f'/session/{session_id}/question')

        resp = client.post(f'/session/{session_id}/answer', data={
            'answer': '',
            'question_id': '1',
            'response_time_s': '0',
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/question' in resp.headers['Location']


class TestDashboard:
    def test_dashboard_index_empty(self, client):
        resp = client.get('/dashboard/')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data

    def test_dashboard_index_with_students(self, client):
        from models import student as student_model
        student_model.create('DashKid')
        resp = client.get('/dashboard/')
        assert resp.status_code == 200
        assert b'DashKid' in resp.data

    def test_dashboard_overview(self, client):
        from models import student as student_model
        sid = student_model.create('OverviewKid')
        resp = client.get(f'/dashboard/{sid}')
        assert resp.status_code == 200
        assert b'OverviewKid' in resp.data
        # Should show grade tree
        assert b'Grade 1' in resp.data
        assert b'Grade 4' in resp.data

    def test_dashboard_overview_nonexistent_student(self, client):
        resp = client.get('/dashboard/9999')
        assert resp.status_code == 302  # Redirects to dashboard index

    def test_full_flow_home_to_dashboard(self, client):
        """Complete flow: home → start → answer → end → dashboard."""
        # Start session
        resp = client.post('/start', data={'student_name': 'FlowKid'},
                           follow_redirects=False)
        location = resp.headers['Location']
        session_id = location.split('/session/')[1].split('/')[0]

        # Get question
        client.get(f'/session/{session_id}/question')

        with client.session_transaction() as sess:
            q = sess.get('current_question', {})
            correct = q.get('correct_answer', '')
            qid = q.get('question_id', '')

        # Answer correctly
        client.post(f'/session/{session_id}/answer', data={
            'answer': correct,
            'question_id': qid,
            'response_time_s': '1.0',
        })

        # End session
        resp = client.get(f'/session/{session_id}/end')
        assert resp.status_code == 200
        assert b'100%' in resp.data  # 1 correct out of 1

        # Check dashboard
        from models import student as student_model
        student = student_model.get_by_name('FlowKid')
        resp = client.get(f'/dashboard/{student["id"]}')
        assert resp.status_code == 200
        assert b'FlowKid' in resp.data
