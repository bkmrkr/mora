"""Tests for question pre-caching."""
from services.question_service import _precache, _precache_lock, pop_cached


def _make_question(node_id=1, node_name='Addition'):
    return {
        'question_id': 99,
        'node_id': node_id,
        'node_name': node_name,
        'content': 'What is 2 + 2?',
        'question_type': 'mcq',
        'options': ['A) 3', 'B) 4', 'C) 5', 'D) 6'],
        'correct_answer': 'B) 4',
        'difficulty': 800,
        'difficulty_score': 3,
        'p_correct': 80,
    }


def _seed_cache(student_id, session_id, question):
    with _precache_lock:
        _precache[(student_id, session_id)] = question


def _clear_cache():
    with _precache_lock:
        _precache.clear()


def test_pop_cached_empty():
    _clear_cache()
    assert pop_cached(1, 'sess-1') is None


def test_pop_cached_returns_question():
    _clear_cache()
    q = _make_question()
    _seed_cache(1, 'sess-1', q)
    result = pop_cached(1, 'sess-1')
    assert result is not None
    assert result['content'] == 'What is 2 + 2?'


def test_pop_cached_removes_entry():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question())
    pop_cached(1, 'sess-1')
    assert pop_cached(1, 'sess-1') is None


def test_pop_cached_wrong_student():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question())
    assert pop_cached(2, 'sess-1') is None


def test_pop_cached_wrong_session():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question())
    assert pop_cached(1, 'sess-2') is None


def test_pop_cached_node_matches():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question(node_id=5))
    result = pop_cached(1, 'sess-1', expected_node_id=5)
    assert result is not None


def test_pop_cached_node_mismatch_returns_none():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question(node_id=5))
    result = pop_cached(1, 'sess-1', expected_node_id=7)
    assert result is None


def test_pop_cached_node_mismatch_clears_cache():
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question(node_id=5))
    pop_cached(1, 'sess-1', expected_node_id=7)
    # Cache should be cleared even on mismatch
    assert pop_cached(1, 'sess-1') is None


def test_pop_cached_no_node_filter():
    """When expected_node_id is None, accept any cached question."""
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question(node_id=99))
    result = pop_cached(1, 'sess-1', expected_node_id=None)
    assert result is not None


def test_cache_overwrites():
    """New precache for same key overwrites old."""
    _clear_cache()
    _seed_cache(1, 'sess-1', _make_question(node_id=1, node_name='Old'))
    _seed_cache(1, 'sess-1', _make_question(node_id=2, node_name='New'))
    result = pop_cached(1, 'sess-1')
    assert result['node_name'] == 'New'
