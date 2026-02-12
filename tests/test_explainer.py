"""Tests for ai/explainer.py — mocking Ollama."""
from unittest.mock import patch
from ai.explainer import explain


def _mock_ask_valid(system, user, **kwargs):
    return (
        '{"encouragement": "Nice try!", "explanation": "Step 1...", '
        '"key_concept": "Addition", "tip": "Practice more"}',
        'test-model',
        f'SYSTEM: {system}\nUSER: {user}',
    )


def _mock_ask_list(system, user, **kwargs):
    """LLM returns a list — parse_ai_json_dict extracts first dict."""
    return (
        '[{"encouragement": "Good effort!", "explanation": "The answer is 4."}]',
        'test-model',
        'prompt',
    )


def _mock_ask_minimal(system, user, **kwargs):
    """Only some fields present."""
    return ('{"explanation": "Just this."}', 'test-model', 'prompt')


@patch('ai.explainer.ask', side_effect=_mock_ask_valid)
def test_returns_dict_and_metadata(mock):
    result, model, prompt = explain('Q?', '4', '3', 'Addition', 'Basic math')
    assert isinstance(result, dict)
    assert result['encouragement'] == 'Nice try!'
    assert result['explanation'] == 'Step 1...'
    assert model == 'test-model'


@patch('ai.explainer.ask', side_effect=_mock_ask_list)
def test_list_response_extracts_dict(mock):
    result, _, _ = explain('Q?', '4', '3', 'Addition', 'Math')
    assert isinstance(result, dict)
    assert 'explanation' in result


@patch('ai.explainer.ask', side_effect=_mock_ask_minimal)
def test_minimal_response(mock):
    result, _, _ = explain('Q?', '4', '3', 'Addition', 'Math')
    assert result['explanation'] == 'Just this.'


@patch('ai.explainer.ask')
def test_malformed_json_raises(mock):
    mock.return_value = ('not json at all', 'test-model', 'prompt')
    import pytest
    with pytest.raises(Exception):
        explain('Q?', '4', '3', 'Addition', 'Math')


@patch('ai.explainer.ask', side_effect=ConnectionError('No Ollama'))
def test_connection_error_propagates(mock):
    import pytest
    with pytest.raises(ConnectionError):
        explain('Q?', '4', '3', 'Addition', 'Math')


@patch('ai.explainer.ask', side_effect=_mock_ask_valid)
def test_prompt_includes_context(mock):
    explain('What is 2+2?', '4', '3', 'Addition', 'Basic arithmetic')
    call_args = mock.call_args[0]
    assert 'What is 2+2?' in call_args[1]
    assert 'Addition' in call_args[1]
