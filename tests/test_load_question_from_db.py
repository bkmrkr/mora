"""Tests for _load_question_from_db — SVG param extraction from content."""
import json
from routes.session import _load_question_from_db
from models import question as question_model
from models import curriculum_node as node_model
from models import topic as topic_model


def _make_question(content, correct_answer, q_type='mcq', options=None):
    """Create a question and return its ID."""
    tid = topic_model.create(f'Topic-{content[:10]}', 'test')
    nid = node_model.create(tid, f'Node-{content[:10]}', 'test')
    return question_model.create(
        curriculum_node_id=nid,
        content=content,
        question_type=q_type,
        options=json.dumps(options) if options else None,
        correct_answer=correct_answer,
        difficulty=500,
    )


def test_clock_params_extracted():
    qid = _make_question(
        'What time does this clock show? [3:00]', '3:00',
        options=['1:00', '3:00', '6:00', '9:00']
    )
    result = _load_question_from_db(qid)
    assert result is not None
    assert result['clock_hour'] == 3
    assert result['clock_minute'] == 0


def test_clock_params_half_hour():
    qid = _make_question(
        'What time does this clock show? [6:30]', '6:30',
        options=['6:00', '6:15', '6:30', '6:45']
    )
    result = _load_question_from_db(qid)
    assert result['clock_hour'] == 6
    assert result['clock_minute'] == 30


def test_inequality_params_extracted():
    qid = _make_question(
        'Which inequality does this number line represent? [x > -5]', 'x > -5',
        options=['x > -5', 'x < -5', 'x >= -5', 'x <= -5']
    )
    result = _load_question_from_db(qid)
    assert result is not None
    assert result['inequality_op'] == '>'
    assert result['inequality_boundary'] == -5


def test_inequality_params_gte():
    qid = _make_question(
        'Which inequality does this number line represent? [x >= 3]', 'x >= 3',
        options=['x > 3', 'x < 3', 'x >= 3', 'x <= 3']
    )
    result = _load_question_from_db(qid)
    assert result['inequality_op'] == '>='
    assert result['inequality_boundary'] == 3


def test_normal_question_no_svg_params():
    qid = _make_question('What is 2+2?', '4', options=['2', '3', '4', '5'])
    result = _load_question_from_db(qid)
    assert result['clock_hour'] is None
    assert result['clock_minute'] is None
    assert result['inequality_op'] is None
    assert result['inequality_boundary'] is None


def test_rejected_question_not_loaded():
    qid = _make_question('Bad question', 'bad')
    from db.database import execute_db
    execute_db("UPDATE questions SET test_status = 'rejected' WHERE id = ?", (qid,))
    result = _load_question_from_db(qid)
    assert result is None
