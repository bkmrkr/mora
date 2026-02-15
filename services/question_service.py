"""Question generation orchestrator — select node, generate, validate, store."""
import json
import logging

from flask import session as flask_session

from models import student_skill as skill_model
from models import attempt as attempt_model
from models import question as question_model
from models import curriculum_node as node_model
from models import topic as topic_model
from models import session as session_model
from engine import elo
from engine import next_question as nq_engine
from engine.question_validator import validate_question
from engine.question_options import QUESTION_TYPE_MCQ
from ai import question_generator
from ai.local_generators import (is_clock_node, generate_clock_question,
                                 is_inequality_node, generate_inequality_question)
from config.settings import SESSION_DEFAULTS

logger = logging.getLogger(__name__)


def generate_next(session_id, student, topic_id, last_was_correct=None):
    """Select focus node, compute difficulty, generate question.

    Dedup: exact match against session + lifetime correctly-answered questions.
    Post-generation validation rejects bad LLM output and retries.

    Returns question_dict or None.
    """
    student_id = student['id']

    # Get context
    recent_attempts = attempt_model.get_recent(student_id, limit=30)
    all_skills = {
        s['curriculum_node_id']: s
        for s in skill_model.get_for_student(student_id)
    }
    nodes = node_model.get_for_topic(topic_id)
    if not nodes:
        flask_session['current_question'] = None
        return None

    # Select focus node
    analysis = nq_engine.analyze_recent(recent_attempts, all_skills)
    current_q = flask_session.get('current_question')
    current_node_id = current_q.get('node_id') if current_q else None
    focus_node_id = nq_engine.select_focus_node(
        analysis, nodes, all_skills, current_node_id, last_was_correct
    )

    if focus_node_id is None:
        flask_session['current_question'] = None
        return None

    focus_node = node_model.get_by_id(focus_node_id)
    topic = topic_model.get_by_id(topic_id)

    # Compute target difficulty and question type
    target_diff, q_type = nq_engine.compute_question_params(
        focus_node_id, all_skills, analysis
    )

    # Dedup sets: session texts + globally correct texts
    session_attempts = attempt_model.get_for_session(session_id)
    session_texts = {a['content'] for a in session_attempts if a.get('content')}
    sess = session_model.get_by_id(session_id)
    if sess and sess.get('current_question_id'):
        current_q_row = question_model.get_by_id(sess['current_question_id'])
        if current_q_row and current_q_row.get('content'):
            session_texts.add(current_q_row['content'])
    global_correct_texts = attempt_model.get_correct_texts(student_id)
    recent_text_list = list(session_texts | global_correct_texts)

    # Try local generators first (clock, inequality)
    node_desc = focus_node.get('description', '')
    q_data = None
    model = None
    prompt = None

    if is_clock_node(focus_node['name'], node_desc):
        q_data, model, prompt = generate_clock_question(
            focus_node['name'], node_desc, recent_text_list
        )
        if q_data:
            q_type = QUESTION_TYPE_MCQ

    if not q_data and is_inequality_node(focus_node['name'], node_desc):
        q_data, model, prompt = generate_inequality_question(
            focus_node['name'], node_desc, recent_text_list
        )
        if q_data:
            q_type = QUESTION_TYPE_MCQ

    # LLM generation with validation + dedup retry
    if not q_data:
        for attempt_num in range(SESSION_DEFAULTS['max_generation_attempts']):
            try:
                q_data, model, prompt = question_generator.generate(
                    focus_node['name'], node_desc,
                    topic['name'] if topic else '', node_desc,
                    target_diff, q_type, recent_text_list,
                )
            except Exception as e:
                logger.warning('Generation attempt %d failed: %s', attempt_num + 1, e)
                q_data = None
                continue

            if not isinstance(q_data, dict) or not q_data.get('question'):
                logger.warning('Generation attempt %d: invalid result', attempt_num + 1)
                q_data = None
                continue

            # Validate structure + math
            is_valid, reason = validate_question(q_data, node_desc)
            if not is_valid:
                logger.warning('Validation rejected (attempt %d): %s', attempt_num + 1, reason)
                q_data = None
                continue

            # MCQ: verify LLM provided valid options
            if q_type == QUESTION_TYPE_MCQ:
                opts = q_data.get('options', [])
                correct = q_data.get('correct_answer', '')
                if not (isinstance(opts, list) and len(opts) >= 3
                        and correct in opts):
                    logger.warning('Invalid MCQ options (attempt %d): %d opts, answer_in=%s',
                                   attempt_num + 1,
                                   len(opts) if isinstance(opts, list) else 0,
                                   correct in opts if isinstance(opts, list) else False)
                    q_data = None
                    continue

            # Exact dedup
            q_text = q_data['question'].strip()
            if q_text in session_texts or q_text in global_correct_texts:
                logger.warning('Dedup rejected (attempt %d)', attempt_num + 1)
                q_data = None
                continue

            break  # passed all checks

    if not q_data:
        flask_session['current_question'] = None
        return None

    # Store in DB
    skill = all_skills.get(focus_node_id, {})
    skill_rating = skill.get('skill_rating', 800.0)
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

    norm_diff = max(0.0, min(1.0, (target_diff - 400) / 800))
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
        'node_description': node_desc,
        'clock_hour': q_data.get('clock_hour'),
        'clock_minute': q_data.get('clock_minute'),
        'inequality_op': q_data.get('inequality_op'),
        'inequality_boundary': q_data.get('inequality_boundary'),
    }

    flask_session['current_question'] = question_dict
    session_model.update_current_question(session_id, question_id)
    return question_dict
