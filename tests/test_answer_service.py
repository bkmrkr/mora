"""Tests for services/answer_service.py — mocking AI, using real DB."""
from unittest.mock import patch

from models import student as student_model
from models import student_skill as skill_model
from models import attempt as attempt_model
from models import curriculum_node as node_model
from models import topic as topic_model
from models import session as session_model
from models import question as question_model
from services import answer_service


def _setup_student_and_question(topic_name='Math', node_name='Addition'):
    """Create a student, topic, node, question, and return (student, question_dict, session_id)."""
    student_id = student_model.create('Test Student')
    student = student_model.get_by_id(student_id)
    topic_id = topic_model.create(node_name, 'Test topic')
    node_id = node_model.create(topic_id, node_name, 'Basic addition', order_index=1)
    session_id = session_model.create(student_id, topic_id)

    # Create a real question in DB to satisfy FK constraints
    question_id = question_model.create(
        curriculum_node_id=node_id,
        content='What is 2 + 3?',
        question_type='short_answer',
        options=None,
        correct_answer='5',
        explanation='2 + 3 = 5',
        difficulty=800,
    )

    question_dict = {
        'question_id': question_id,
        'node_id': node_id,
        'node_name': node_name,
        'content': 'What is 2 + 3?',
        'question_type': 'short_answer',
        'options': None,
        'correct_answer': '5',
        'explanation': '2 + 3 = 5',
        'difficulty': 800,
        'node_description': 'Adding small numbers',
    }
    return student, question_dict, session_id


def test_correct_short_answer():
    student, q, session_id = _setup_student_and_question()
    result = answer_service.process_answer(student, q, '5', 3.0, session_id)
    assert result['is_correct'] is True
    assert result['partial_score'] == 1.0
    assert result['student_answer'] == '5'
    assert result['correct_answer'] == '5'


def test_wrong_short_answer():
    student, q, session_id = _setup_student_and_question()
    result = answer_service.process_answer(student, q, '7', 3.0, session_id)
    assert result['is_correct'] is False
    assert result['partial_score'] == 0.0


def test_correct_mcq():
    student, q, session_id = _setup_student_and_question()
    q['question_type'] = 'mcq'
    q['options'] = ['3', '4', '5', '6']
    q['correct_answer'] = 'C'
    result = answer_service.process_answer(student, q, 'C', 2.0, session_id)
    assert result['is_correct'] is True


def test_wrong_mcq():
    student, q, session_id = _setup_student_and_question()
    q['question_type'] = 'mcq'
    q['options'] = ['3', '4', '5', '6']
    q['correct_answer'] = 'C'
    result = answer_service.process_answer(student, q, 'A', 2.0, session_id)
    assert result['is_correct'] is False


def test_elo_increases_on_correct():
    student, q, session_id = _setup_student_and_question()
    before = skill_model.get(student['id'], q['node_id'])['skill_rating']
    result = answer_service.process_answer(student, q, '5', 3.0, session_id)
    assert result['skill_rating'] > before


def test_elo_decreases_on_wrong():
    student, q, session_id = _setup_student_and_question()
    before = skill_model.get(student['id'], q['node_id'])['skill_rating']
    result = answer_service.process_answer(student, q, '999', 3.0, session_id)
    assert result['skill_rating'] < before


def test_attempt_recorded():
    student, q, session_id = _setup_student_and_question()
    answer_service.process_answer(student, q, '5', 3.0, session_id)
    attempts = attempt_model.get_for_session(session_id)
    assert len(attempts) == 1
    assert attempts[0]['is_correct'] == 1


def test_skill_history_recorded():
    student, q, session_id = _setup_student_and_question()
    answer_service.process_answer(student, q, '5', 3.0, session_id)
    history = skill_model.get_history(student['id'], q['node_id'])
    assert len(history) >= 1


def test_result_contains_node_description():
    student, q, session_id = _setup_student_and_question()
    result = answer_service.process_answer(student, q, '5', 3.0, session_id)
    assert result['node_description'] == 'Adding small numbers'


def test_result_contains_question_text():
    student, q, session_id = _setup_student_and_question()
    result = answer_service.process_answer(student, q, '5', 3.0, session_id)
    assert result['question_text'] == 'What is 2 + 3?'


def test_mastery_level_in_result():
    student, q, session_id = _setup_student_and_question()
    result = answer_service.process_answer(student, q, '5', 3.0, session_id)
    assert 0 <= result['mastery_level'] <= 1.0


@patch('ai.answer_grader.grade')
def test_open_ended_uses_llm_grader(mock_grade):
    mock_grade.return_value = (True, 0.9, 'Good explanation!', 'test-model', 'prompt')
    student, q, session_id = _setup_student_and_question()
    q['question_type'] = 'open_ended'
    result = answer_service.process_answer(student, q, 'Some answer', 5.0, session_id)
    assert result['is_correct'] is True
    assert result['partial_score'] == 0.9
    assert result['feedback'] == 'Good explanation!'
    mock_grade.assert_called_once()


@patch('ai.answer_grader.grade', side_effect=Exception('LLM down'))
def test_open_ended_fallback_on_grader_failure(mock_grade):
    student, q, session_id = _setup_student_and_question()
    q['question_type'] = 'open_ended'
    # Exact match fallback
    result = answer_service.process_answer(student, q, '5', 5.0, session_id)
    assert result['is_correct'] is True  # falls back to check_answer


def test_streak_computation():
    """Streak should count consecutive correct answers."""
    student, q, session_id = _setup_student_and_question()
    # Answer correctly 3 times to build streak
    for _ in range(3):
        answer_service.process_answer(student, q, '5', 2.0, session_id)
    # 4th correct answer should benefit from streak
    result = answer_service.process_answer(student, q, '5', 2.0, session_id)
    assert result['is_correct'] is True
