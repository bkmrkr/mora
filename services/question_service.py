"""Question generation orchestrator with validation, dedup, and pre-caching."""
import json
import logging
import threading

from flask import session as flask_session

from models import student_skill as skill_model
from models import attempt as attempt_model
from models import question as question_model
from models import curriculum_node as node_model
from models import topic as topic_model
from engine import elo
from engine import next_question as nq_engine
from engine.question_validator import validate_question
from ai import question_generator
from ai.local_generators import is_clock_node, generate_clock_question
from config.settings import SESSION_DEFAULTS

logger = logging.getLogger(__name__)

# Pre-cache: one question per (student_id, session_id)
_precache = {}
_precache_lock = threading.Lock()


def pop_cached(student_id, session_id, expected_node_id=None):
    """Return and remove a pre-cached question if available and node matches.

    Returns question_dict or None.
    """
    key = (student_id, session_id)
    with _precache_lock:
        cached = _precache.pop(key, None)
    if cached is None:
        return None
    if expected_node_id is not None and cached.get('node_id') != expected_node_id:
        logger.info('Pre-cache miss: node changed (%s → %s)', cached.get('node_id'), expected_node_id)
        return None
    logger.info('Pre-cache hit for student %d session %s', student_id, session_id)
    return cached


def precache_next(session_id, student, topic_id):
    """Pre-generate and cache the next question (called from background request)."""
    question_dict = generate_next(session_id, student, topic_id, store_in_session=False)
    if question_dict:
        key = (student['id'], session_id)
        with _precache_lock:
            _precache[key] = question_dict
        logger.info('Pre-cached question for student %d session %s (node: %s)',
                     student['id'], session_id, question_dict.get('node_name'))
    return question_dict


def generate_next(session_id, student, topic_id, store_in_session=True):
    """Select focus node, compute difficulty, generate question.

    Three dedup layers (from kidtutor):
      1. Session dedup — never repeat any question within the same session
      2. Global dedup — never repeat a correctly-answered question (lifetime)
      3. Recent texts — passed to LLM to avoid similar questions

    Post-generation validation rejects bad LLM output and retries.

    When store_in_session=True, stores in flask_session['current_question'].
    When False (pre-caching), skips session writes.
    Returns question_dict or None.
    """
    student_id = student['id']

    # Get recent 30 attempts
    recent_attempts = attempt_model.get_recent(student_id, limit=30)

    # Get all student_skill records
    all_skills = {
        s['curriculum_node_id']: s
        for s in skill_model.get_for_student(student_id)
    }

    # Get curriculum nodes for this topic
    nodes = node_model.get_for_topic(topic_id)
    if not nodes:
        if store_in_session:
            flask_session['current_question'] = None
        return None

    # Analyze recent history
    analysis = nq_engine.analyze_recent(recent_attempts, all_skills)

    # Select focus node
    current_node_id = None
    if store_in_session:
        current_q = flask_session.get('current_question')
        current_node_id = current_q.get('node_id') if current_q else None
    focus_node_id = nq_engine.select_focus_node(
        analysis, nodes, all_skills, current_node_id
    )

    if focus_node_id is None:
        if store_in_session:
            flask_session['current_question'] = None
        return None

    focus_node = node_model.get_by_id(focus_node_id)
    topic = topic_model.get_by_id(topic_id)

    # Compute target difficulty and question type
    target_diff, q_type = nq_engine.compute_question_params(
        focus_node_id, all_skills, analysis
    )

    # --- Dedup layers ---
    # Layer 1: Session dedup — all question texts in this session
    session_attempts = attempt_model.get_for_session(session_id)
    session_texts = {a['content'] for a in session_attempts if a.get('content')}

    # Layer 2: Global dedup — all correctly-answered question texts (lifetime)
    global_correct_texts = attempt_model.get_correct_texts(student_id)

    # Combined exclude set for LLM prompt
    all_exclude = session_texts | global_correct_texts
    recent_text_list = list(all_exclude)

    # --- Check for local generators (no LLM needed) ---
    node_desc = focus_node.get('description', '')
    q_data = None
    model = None
    prompt = None

    if is_clock_node(focus_node['name'], node_desc):
        q_data, model, prompt = generate_clock_question(
            focus_node['name'], node_desc, recent_text_list
        )
        if q_data:
            q_type = 'mcq'  # clock questions are always MCQ
            logger.info('Generated local clock question for "%s"', focus_node['name'])

    # --- Generate with validation + dedup retry (LLM path) ---
    if not q_data:
        for attempt_num in range(SESSION_DEFAULTS['max_generation_attempts']):
            try:
                q_data, model, prompt = question_generator.generate(
                    focus_node['name'],
                    node_desc,
                    topic['name'] if topic else '',
                    node_desc,
                    target_diff,
                    q_type,
                    recent_text_list,
                )
            except Exception as e:
                logger.warning('Generation attempt %d failed: %s', attempt_num + 1, e)
                q_data = None
                continue

            if not q_data or not q_data.get('question'):
                logger.warning('Generation attempt %d: empty question', attempt_num + 1)
                q_data = None
                continue

            # Validate the generated question
            is_valid, reason = validate_question(q_data, node_desc)
            if not is_valid:
                logger.warning('Validation rejected (attempt %d): %s', attempt_num + 1, reason)
                q_data = None
                continue

            # Dedup check: reject if question already seen in session or globally
            q_text = q_data['question'].strip()
            if q_text in session_texts:
                logger.warning('Session dedup rejected (attempt %d)', attempt_num + 1)
                q_data = None
                continue

            if q_text in global_correct_texts:
                logger.warning('Global dedup rejected (attempt %d)', attempt_num + 1)
                q_data = None
                continue

            # Passed all checks
            break

    if not q_data:
        if store_in_session:
            flask_session['current_question'] = None
        return None

    # Store question in DB
    skill = all_skills.get(focus_node_id, {})
    skill_rating = skill.get('skill_rating', 1000.0)
    p_correct = elo.p_correct(skill_rating, target_diff)

    question_id = question_model.create(
        curriculum_node_id=focus_node_id,
        content=q_data.get('question', ''),
        question_type=q_type,
        options=json.dumps(q_data.get('options')) if q_data.get('options') else None,
        correct_answer=q_data.get('correct_answer', ''),
        explanation=q_data.get('explanation', ''),
        difficulty=target_diff,
        estimated_p_correct=p_correct,
        generated_prompt=prompt,
        model_used=model,
    )

    # Compute difficulty score (1-10) for display
    norm_diff = max(0.0, min(1.0, (target_diff - 500) / 600))
    difficulty_score = round(norm_diff * 9) + 1

    question_dict = {
        'question_id': question_id,
        'node_id': focus_node_id,
        'node_name': focus_node['name'],
        'content': q_data.get('question', ''),
        'question_type': q_type,
        'options': q_data.get('options'),
        'correct_answer': q_data.get('correct_answer', ''),
        'explanation': q_data.get('explanation', ''),
        'difficulty': target_diff,
        'difficulty_score': difficulty_score,
        'p_correct': round(p_correct * 100),
        'clock_svg': q_data.get('clock_svg'),
    }
    if store_in_session:
        flask_session['current_question'] = question_dict
    return question_dict
