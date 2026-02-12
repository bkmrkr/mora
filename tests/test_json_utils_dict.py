"""Tests for parse_ai_json_dict() — guarantees dict return from LLM output."""
import pytest
from ai.json_utils import parse_ai_json_dict, parse_ai_json, _fix_latex_escapes


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


# --- LaTeX escape handling ---

def test_latex_sqrt_and_times():
    r"""LLM returns \(\sqrt{16} \times \sqrt{9}\) — invalid JSON escapes."""
    raw = r'{"question": "Simplify: \(\sqrt{16} \times \sqrt{9}\)", "correct_answer": "12"}'
    result = parse_ai_json_dict(raw)
    assert result['correct_answer'] == '12'
    assert 'sqrt' in result['question']


def test_latex_frac():
    r"""LLM returns \frac{1}{2} — \f is a valid JSON escape (formfeed)."""
    raw = r'{"question": "What is \frac{1}{2}?", "correct_answer": "0.5"}'
    result = parse_ai_json_dict(raw)
    assert result['correct_answer'] == '0.5'


def test_latex_newline_in_explanation():
    r"""LLM uses \n inside LaTeX which is also a valid JSON escape."""
    raw = r'{"question": "Q?", "correct_answer": "4", "explanation": "Step 1\nStep 2"}'
    # This is valid JSON (\n = newline) — should parse normally
    result = parse_ai_json_dict(raw)
    assert result['correct_answer'] == '4'


def test_fix_escapes_preserves_quotes():
    r"""\" must stay as \" for JSON to parse."""
    raw = r'{"key": "value with \"quotes\""}'
    fixed = _fix_latex_escapes(raw)
    result = parse_ai_json(fixed)
    assert 'quotes' in result['key']


def test_fix_escapes_preserves_backslash():
    r"""\\ must stay as \\."""
    raw = r'{"key": "path\\to\\file"}'
    fixed = _fix_latex_escapes(raw)
    result = parse_ai_json(fixed)
    assert 'path' in result['key']
