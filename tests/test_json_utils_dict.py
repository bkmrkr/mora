"""Tests for parse_ai_json_dict() — guarantees dict return from LLM output."""
import pytest
from ai.json_utils import parse_ai_json_dict


def test_dict_passthrough():
    assert parse_ai_json_dict('{"key": "value"}') == {"key": "value"}


def test_extracts_first_dict_from_list():
    text = '[{"question": "What?"}, {"question": "How?"}]'
    assert parse_ai_json_dict(text) == {"question": "What?"}


def test_skips_non_dict_list_items():
    text = '[1, "hello", {"found": true}]'
    assert parse_ai_json_dict(text) == {"found": True}


def test_rejects_list_of_non_dicts():
    with pytest.raises(ValueError, match="no dict elements"):
        parse_ai_json_dict('[1, 2, 3]')


def test_rejects_empty_list():
    with pytest.raises(ValueError, match="no dict elements"):
        parse_ai_json_dict('[]')


def test_rejects_string():
    with pytest.raises((ValueError, Exception)):
        parse_ai_json_dict('"just a string"')


def test_rejects_number():
    with pytest.raises((ValueError, Exception)):
        parse_ai_json_dict('42')


def test_rejects_null():
    with pytest.raises((ValueError, Exception)):
        parse_ai_json_dict('null')


def test_markdown_code_block():
    text = '```json\n{"question": "What is 2+2?"}\n```'
    assert parse_ai_json_dict(text) == {"question": "What is 2+2?"}


def test_nested_objects():
    text = '{"a": {"b": 1}, "c": [1,2]}'
    result = parse_ai_json_dict(text)
    assert result == {"a": {"b": 1}, "c": [1, 2]}


def test_whitespace_only_raises():
    with pytest.raises(Exception):
        parse_ai_json_dict('   \n\n  ')


def test_surrounding_text():
    text = 'Here is the answer:\n{"x": 1}\nDone.'
    assert parse_ai_json_dict(text) == {"x": 1}
