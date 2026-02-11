"""Tests for ai/json_utils.py."""
import pytest
from ai.json_utils import parse_ai_json


def test_raw_json():
    result = parse_ai_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_markdown_json():
    text = '```json\n{"key": "value"}\n```'
    result = parse_ai_json(text)
    assert result == {"key": "value"}


def test_markdown_no_lang():
    text = '```\n{"key": "value"}\n```'
    result = parse_ai_json(text)
    assert result == {"key": "value"}


def test_json_with_surrounding_text():
    text = 'Here is the result:\n{"key": "value"}\nDone!'
    result = parse_ai_json(text)
    assert result == {"key": "value"}


def test_invalid_json_raises():
    with pytest.raises(Exception):
        parse_ai_json("not json at all")


def test_array_json():
    result = parse_ai_json('[1, 2, 3]')
    assert result == [1, 2, 3]
