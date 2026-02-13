"""Tests for services/question_service.py — mocking AI generator, using real DB."""
import json
from unittest.mock import patch, MagicMock

from flask import session as flask_session

from models import student as student_model
from models import student_skill as skill_model
from models import attempt as attempt_model
from models import curriculum_node as node_model
from models import topic as topic_model
from models import session as session_model
from models import question as question_model
from services import question_service


def _valid_q_data():
    return {
        'question': 'What is 7 + 5?',
        'correct_answer': '12',
        'options': None,
        'explanation': '7 + 5 = 12',
    }


def _valid_mcq_data():
    return {
        'question': 'What is 3 × 4?',
        'correct_answer': 'B',
        'options': ['A) 7', 'B) 12', 'C) 15', 'D) 10'],
        'explanation': '3 × 4 = 12',
    }


def _setup(app):
    """Create student, topic, node, session inside app context."""
    with app.app_context():
        student_id = student_model.create('Test Student')
        student = student_model.get_by_id(student_id)
        topic_id = topic_model.create('Math', 'Basic math')
        node_id = node_model.create(topic_id, 'Addition', 'Adding numbers', order_index=1)
        session_id = session_model.create(student_id, topic_id)
        return student, topic_id, node_id, session_id


def _mock_generator(q_data):
    """Create a mock that returns (q_data, model, prompt)."""
    def _gen(*args, **kwargs):
        return q_data, 'test-model', 'test-prompt'
    return _gen


@patch('services.question_service.question_generator.generate')
def test_generate_next_stores_in_session(mock_gen, app):
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        with app.test_client() as c:
            with c.session_transaction():
                pass
            result = question_service.generate_next(session_id, student, topic_id)
    assert result is not None
    assert result['content'] == 'What is 7 + 5?'
    # correct_answer now includes letter prefix from computed distractors
    assert result['correct_answer'].endswith('12')
    assert result['options'] is not None  # Computed distractors


@patch('services.question_service.question_generator.generate')
def test_generate_next_returns_none_on_failure(mock_gen, app):
    mock_gen.side_effect = Exception('LLM down')
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is None


@patch('services.question_service.question_generator.generate')
def test_type_guard_rejects_list(mock_gen, app):
    """If generator returns a list instead of dict, retry and eventually return None."""
    mock_gen.return_value = ([{'question': 'Q?'}], 'model', 'prompt')
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is None


@patch('services.question_service.question_generator.generate')
def test_dedup_rejects_repeated_question(mock_gen, app):
    """Same question text in session should be rejected."""
    student, topic_id, node_id, session_id = _setup(app)

    # First call succeeds
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    with app.test_request_context():
        result1 = question_service.generate_next(session_id, student, topic_id)
    assert result1 is not None

    # Record an attempt so the question text is in session history
    attempt_model.create(
        question_id=result1['question_id'],
        student_id=student['id'],
        session_id=session_id,
        answer_given='12',
        is_correct=1,
        partial_score=1.0,
        response_time_seconds=2.0,
        curriculum_node_id=node_id,
        skill_rating_before=800,
        skill_rating_after=820,
    )

    # Second call with same text should be rejected
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    with app.test_request_context():
        result2 = question_service.generate_next(session_id, student, topic_id)
    # Result is None because all attempts produce dedup matches
    assert result2 is None


@patch('services.question_service.question_generator.generate')
def test_question_stored_in_db(mock_gen, app):
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is not None
    # Verify DB record exists
    q_row = question_model.get_by_id(result['question_id'])
    assert q_row is not None
    assert q_row['content'] == 'What is 7 + 5?'


@patch('services.question_service.question_generator.generate')
def test_node_description_in_result(mock_gen, app):
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is not None
    assert result.get('node_description') == 'Adding numbers'


@patch('services.question_service.question_generator.generate')
def test_difficulty_score_1_to_10(mock_gen, app):
    mock_gen.side_effect = _mock_generator(_valid_q_data())
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is not None
    assert 1 <= result['difficulty_score'] <= 10


def test_pop_cached_returns_none_when_empty():
    result = question_service.pop_cached(999, 'nonexistent-session')
    assert result is None


@patch('services.question_service.question_generator.generate')
def test_empty_question_rejected(mock_gen, app):
    """Empty question field should be rejected."""
    bad_data = {'question': '', 'correct_answer': '5', 'explanation': 'x'}
    mock_gen.return_value = (bad_data, 'model', 'prompt')
    student, topic_id, node_id, session_id = _setup(app)
    with app.test_request_context():
        result = question_service.generate_next(session_id, student, topic_id)
    assert result is None
