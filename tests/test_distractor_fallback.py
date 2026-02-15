"""Tests for MCQ distractor handling.

Hebrew questions use LLM-provided options (not algorithmic distractors).
English questions use computed distractors as before.
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
def test_hebrew_with_llm_options_stays_mcq(mock_session, mock_gen):
    """Hebrew answers with LLM-provided options should stay MCQ."""
    student, tid, nid = _setup()

    # Mock: LLM returns a Hebrew answer WITH 4 options (new behavior)
    mock_gen.return_value = (
        {
            'question': 'What is the Hebrew word for dog?',
            'correct_answer': '\u05DB\u05DC\u05D1',  # כלב
            'options': ['\u05D7\u05EA\u05D5\u05DC', '\u05DB\u05DC\u05D1',
                        '\u05E1\u05E4\u05E8', '\u05D1\u05D9\u05EA'],
            'explanation': 'The Hebrew word for dog is kelev.',
            '_llm_provided_options': True,
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
    assert '\u05DB\u05DC\u05D1' in result['options']


@patch('services.question_service.question_generator.generate')
@patch('services.question_service.session_model')
def test_hebrew_invalid_llm_options_retries(mock_session, mock_gen):
    """Hebrew answers with invalid LLM options (wrong count) should retry."""
    student, tid, nid = _setup()

    # First call: bad options (only 2), second call: valid options
    mock_gen.side_effect = [
        (
            {
                'question': 'What is the Hebrew word for cat?',
                'correct_answer': '\u05D7\u05EA\u05D5\u05DC',
                'options': ['\u05D7\u05EA\u05D5\u05DC', '\u05DB\u05DC\u05D1'],  # only 2
                'explanation': 'The Hebrew word for cat is chatul.',
                '_llm_provided_options': True,
            },
            'test-model',
            'test-prompt',
        ),
        (
            {
                'question': 'What is the Hebrew word for house?',
                'correct_answer': '\u05D1\u05D9\u05EA',
                'options': ['\u05E1\u05E4\u05E8', '\u05D1\u05D9\u05EA',
                            '\u05DB\u05DC\u05D1', '\u05D7\u05EA\u05D5\u05DC'],
                'explanation': 'The Hebrew word for house is bayit.',
                '_llm_provided_options': True,
            },
            'test-model',
            'test-prompt',
        ),
    ]
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
    assert len(result['options']) == 4
    # Should have retried — used the second response
    assert result['correct_answer'] == '\u05D1\u05D9\u05EA'


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
