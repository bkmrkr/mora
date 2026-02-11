"""Tests for dual question pre-caching (correct/wrong paths)."""
from services.question_service import _precache, _precache_lock, pop_cached


def _make_question(node_id=1, node_name='Addition', difficulty=800):
    return {
        'question_id': 99,
        'node_id': node_id,
        'node_name': node_name,
        'content': 'What is 2 + 2?',
        'question_type': 'mcq',
        'options': ['A) 3', 'B) 4', 'C) 5', 'D) 6'],
        'correct_answer': 'B) 4',
        'difficulty': difficulty,
        'difficulty_score': 3,
        'p_correct': 80,
    }


def _seed_dual(student_id, session_id, q_correct, q_wrong):
    """Seed cache with dual-path entry."""
    with _precache_lock:
        _precache[(student_id, session_id)] = {
            'correct': q_correct,
            'wrong': q_wrong,
        }


def _clear_cache():
    with _precache_lock:
        _precache.clear()


# --- Empty cache ---

def test_pop_cached_empty():
    _clear_cache()
    assert pop_cached(1, 'sess-1') is None


def test_pop_cached_empty_wrong_path():
    _clear_cache()
    assert pop_cached(1, 'sess-1', is_correct=False) is None


# --- Correct path ---

def test_pop_correct_returns_question():
    _clear_cache()
    q = _make_question(difficulty=850)
    _seed_dual(1, 'sess-1', q_correct=q, q_wrong=_make_question(difficulty=700))
    result = pop_cached(1, 'sess-1', is_correct=True)
    assert result is not None
    assert result['difficulty'] == 850


# --- Wrong path ---

def test_pop_wrong_returns_question():
    _clear_cache()
    q = _make_question(difficulty=700)
    _seed_dual(1, 'sess-1', q_correct=_make_question(difficulty=850), q_wrong=q)
    result = pop_cached(1, 'sess-1', is_correct=False)
    assert result is not None
    assert result['difficulty'] == 700


# --- Dual questions have different difficulties ---

def test_dual_cache_different_difficulties():
    _clear_cache()
    q_correct = _make_question(difficulty=850)
    q_wrong = _make_question(difficulty=700)
    _seed_dual(1, 'sess-1', q_correct, q_wrong)
    # Pop consumes both — test before popping
    with _precache_lock:
        entry = _precache[(1, 'sess-1')]
    assert entry['correct']['difficulty'] == 850
    assert entry['wrong']['difficulty'] == 700
    assert entry['correct']['difficulty'] > entry['wrong']['difficulty']


# --- Pop removes entire entry ---

def test_pop_removes_entry():
    _clear_cache()
    _seed_dual(1, 'sess-1', _make_question(), _make_question())
    pop_cached(1, 'sess-1', is_correct=True)
    # Both paths cleared after one pop
    assert pop_cached(1, 'sess-1', is_correct=False) is None


# --- Wrong student / session ---

def test_pop_wrong_student():
    _clear_cache()
    _seed_dual(1, 'sess-1', _make_question(), _make_question())
    assert pop_cached(2, 'sess-1') is None


def test_pop_wrong_session():
    _clear_cache()
    _seed_dual(1, 'sess-1', _make_question(), _make_question())
    assert pop_cached(1, 'sess-2') is None


# --- None in one path ---

def test_pop_correct_when_wrong_is_none():
    """If wrong-path generation failed, correct-path still works."""
    _clear_cache()
    _seed_dual(1, 'sess-1', q_correct=_make_question(), q_wrong=None)
    result = pop_cached(1, 'sess-1', is_correct=True)
    assert result is not None


def test_pop_wrong_when_correct_is_none():
    """If correct-path generation failed, wrong-path still works."""
    _clear_cache()
    _seed_dual(1, 'sess-1', q_correct=None, q_wrong=_make_question())
    result = pop_cached(1, 'sess-1', is_correct=False)
    assert result is not None


def test_pop_returns_none_when_requested_path_is_none():
    _clear_cache()
    _seed_dual(1, 'sess-1', q_correct=None, q_wrong=_make_question())
    result = pop_cached(1, 'sess-1', is_correct=True)
    assert result is None


# --- Overwrite ---

def test_cache_overwrites():
    """New precache for same key overwrites old."""
    _clear_cache()
    _seed_dual(1, 'sess-1', _make_question(node_name='Old'), _make_question(node_name='Old'))
    _seed_dual(1, 'sess-1', _make_question(node_name='New'), _make_question(node_name='New'))
    result = pop_cached(1, 'sess-1', is_correct=True)
    assert result['node_name'] == 'New'


# --- Default is_correct=True ---

def test_pop_default_is_correct_path():
    """pop_cached() without is_correct defaults to correct path."""
    _clear_cache()
    q_correct = _make_question(difficulty=850)
    q_wrong = _make_question(difficulty=700)
    _seed_dual(1, 'sess-1', q_correct, q_wrong)
    result = pop_cached(1, 'sess-1')
    assert result['difficulty'] == 850
