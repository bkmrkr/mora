"""Tests for _inject_svgs — SVG regeneration from stored params."""
from routes.session import _inject_svgs


def test_inject_clock_svg():
    q = {'clock_hour': 3, 'clock_minute': 0}
    _inject_svgs(q)
    assert 'clock_svg' in q
    assert q['clock_svg'].startswith('<svg')
    assert '</svg>' in q['clock_svg']


def test_inject_inequality_svg():
    q = {'inequality_op': '>', 'inequality_boundary': 5}
    _inject_svgs(q)
    assert 'number_line_svg' in q
    assert q['number_line_svg'].startswith('<svg')
    assert '</svg>' in q['number_line_svg']


def test_inject_no_params_does_nothing():
    q = {'content': 'What is 2+2?', 'clock_hour': None, 'inequality_op': None}
    _inject_svgs(q)
    assert 'clock_svg' not in q
    assert 'number_line_svg' not in q


def test_inject_none_dict_returns_none():
    result = _inject_svgs(None)
    assert result is None


def test_inject_both_types():
    """Only one should be set at a time, but test that both paths work independently."""
    clock_q = {'clock_hour': 12, 'clock_minute': 30}
    _inject_svgs(clock_q)
    assert 'clock_svg' in clock_q

    ineq_q = {'inequality_op': '<=', 'inequality_boundary': -3}
    _inject_svgs(ineq_q)
    assert 'number_line_svg' in ineq_q
