"""Tests for MCQ distractor fallback to short_answer.

When distractor generation fails (Hebrew, non-Latin scripts), the question
should fall back to short_answer type instead of being discarded entirely.
"""
from unittest.mock import patch, MagicMock
from models import topic as topic_model
from models import curriculum_node as node_model
from models import student as student_model
from models import student_skill as skill_model
from services import question_service


def _setup(topic_name='Hebrew', node_name='Vocabulary'):
    """Create test data for Hebrew topic."""
    sid = student_model.create('TestStudent')
    tid = topic_model.create(topic_name, 'Hebrew language')
    nid = node_model.create(tid, node_name, 'Hebrew vocabulary words')
    student = student_model.get_by_id(sid)
    return student, tid, nid


@patch('services.question_service.question_generator.generate')
@patch('services.question_service.session_model')
def test_hebrew_answer_falls_back_to_short_answer(mock_session, mock_gen):
    """Hebrew answers that fail distractor generation should become short_answer."""
    student, tid, nid = _setup()

    # Mock: LLM returns a Hebrew answer that can't generate distractors
    mock_gen.return_value = (
        {
            'question': 'What is the Hebrew word for dog?',
            'correct_answer': '\u05DB\u05DC\u05D1',  # כלב
            'explanation': 'The Hebrew word for dog is kelev.',
        },
        'test-model',
        'test-prompt',
    )
    mock_session.get_by_id.return_value = {
        'id': 'test-session', 'student_id': student['id'],
        'topic_id': tid, 'current_question_id': None,
    }

    with patch('services.question_service.flask_session', {}):
        result = question_service.generate_next(
            'test-session', student, tid, store_in_session=False
        )

    # Should NOT be None — the question should be accepted as short_answer
    assert result is not None
    assert result['question_type'] == 'short_answer'
    assert result['options'] is None
    assert result['correct_answer'] == '\u05DB\u05DC\u05D1'


@patch('services.question_service.question_generator.generate')
@patch('services.question_service.session_model')
def test_english_answer_stays_mcq(mock_session, mock_gen):
    """English numeric answers should still produce MCQ questions."""
    student, tid, nid = _setup('Math', 'Addition')

    mock_gen.return_value = (
        {
            'question': 'What is 5 + 3?',
            'correct_answer': '8',
            'explanation': '5 + 3 = 8',
        },
        'test-model',
        'test-prompt',
    )
    mock_session.get_by_id.return_value = {
        'id': 'test-session', 'student_id': student['id'],
        'topic_id': tid, 'current_question_id': None,
    }

    with patch('services.question_service.flask_session', {}):
        result = question_service.generate_next(
            'test-session', student, tid, store_in_session=False
        )

    assert result is not None
    assert result['question_type'] == 'mcq'
    assert result['options'] is not None
    assert len(result['options']) == 4
