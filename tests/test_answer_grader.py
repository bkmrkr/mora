"""Tests for ai/answer_grader.py — mocking Ollama."""
from unittest.mock import patch
from ai.answer_grader import grade


def _mock_ask(system, user, **kwargs):
    """Return a valid grading JSON response."""
    return (
        '{"is_correct": true, "partial_score": 1.0, "feedback": "Perfect!"}',
        'test-model',
        f'SYSTEM: {system}\nUSER: {user}',
    )


def _mock_ask_wrong(system, user, **kwargs):
    return (
        '{"is_correct": false, "partial_score": 0.3, "feedback": "Close but not quite."}',
        'test-model',
        f'SYSTEM: {system}\nUSER: {user}',
    )


def _mock_ask_partial(system, user, **kwargs):
    return (
        '{"is_correct": false, "partial_score": 0.7, "feedback": "Mostly right."}',
        'test-model',
        f'SYSTEM: {system}\nUSER: {user}',
    )


def _mock_ask_minimal(system, user, **kwargs):
    """Missing optional fields."""
    return ('{"is_correct": true}', 'test-model', 'prompt')


def _mock_ask_list(system, user, **kwargs):
    """LLM returns a list — should be caught by parse_ai_json_dict."""
    return ('[{"is_correct": true, "partial_score": 1.0, "feedback": "Ok"}]', 'test-model', 'prompt')


@patch('ai.answer_grader.ask', side_effect=_mock_ask)
def test_correct_answer(mock):
    is_correct, score, feedback, model, prompt = grade('Q?', 'A', 'A', 'Math')
    assert is_correct is True
    assert score == 1.0
    assert feedback == 'Perfect!'
    assert model == 'test-model'


@patch('ai.answer_grader.ask', side_effect=_mock_ask_wrong)
def test_wrong_answer(mock):
    is_correct, score, feedback, _, _ = grade('Q?', 'A', 'B', 'Math')
    assert is_correct is False
    assert score == 0.3
    assert 'Close' in feedback


@patch('ai.answer_grader.ask', side_effect=_mock_ask_partial)
def test_partial_credit(mock):
    is_correct, score, feedback, _, _ = grade('Q?', 'A', 'B', 'Math')
    assert is_correct is False
    assert score == 0.7


@patch('ai.answer_grader.ask', side_effect=_mock_ask_minimal)
def test_missing_fields_defaults(mock):
    is_correct, score, feedback, _, _ = grade('Q?', 'A', 'A', 'Math')
    assert is_correct is True
    assert score == 1.0  # default when correct
    assert feedback == ''


@patch('ai.answer_grader.ask', side_effect=_mock_ask_list)
def test_list_response_extracts_dict(mock):
    """parse_ai_json_dict should extract dict from list."""
    is_correct, score, feedback, _, _ = grade('Q?', 'A', 'A', 'Math')
    assert is_correct is True


@patch('ai.answer_grader.ask', side_effect=ConnectionError('No Ollama'))
def test_connection_error_propagates(mock):
    """ConnectionError should propagate — caller handles fallback."""
    import pytest
    with pytest.raises(ConnectionError):
        grade('Q?', 'A', 'A', 'Math')


@patch('ai.answer_grader.ask')
def test_malformed_json_raises(mock):
    mock.return_value = ('not json', 'test-model', 'prompt')
    import pytest
    with pytest.raises(Exception):
        grade('Q?', 'A', 'A', 'Math')


@patch('ai.answer_grader.ask', side_effect=_mock_ask)
def test_prompt_includes_question(mock):
    grade('What is 2+2?', '4', '3', 'Arithmetic')
    call_args = mock.call_args[0]
    assert 'What is 2+2?' in call_args[1]
    assert 'Arithmetic' in call_args[1]
