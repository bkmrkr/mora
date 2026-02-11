"""Question generation orchestrator."""
import json
import logging

from flask import session as flask_session

from models import student_skill as skill_model
from models import attempt as attempt_model
from models import question as question_model
from models import curriculum_node as node_model
from models import topic as topic_model
from engine import elo
from engine import next_question as nq_engine
from ai import question_generator
from config.settings import SESSION_DEFAULTS

logger = logging.getLogger(__name__)


def generate_next(session_id, student, topic_id):
    """Select focus node, compute difficulty, generate question.

    Stores question in flask_session['current_question'].
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
        flask_session['current_question'] = None
        return None

    # Analyze recent history
    analysis = nq_engine.analyze_recent(recent_attempts, all_skills)

    # Select focus node
    current_q = flask_session.get('current_question')
    current_node_id = current_q.get('node_id') if current_q else None
    focus_node_id = nq_engine.select_focus_node(
        analysis, nodes, all_skills, current_node_id
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

    # Get recent question texts for dedup
    session_attempts = attempt_model.get_for_session(session_id)
    recent_texts = [a['content'] for a in session_attempts if a.get('content')]

    # Generate question via Ollama (with retry)
    q_data = None
    model = None
    prompt = None
    for attempt_num in range(SESSION_DEFAULTS['max_generation_attempts']):
        try:
            q_data, model, prompt = question_generator.generate(
                focus_node['name'],
                focus_node.get('description', ''),
                topic['name'] if topic else '',
                '',
                target_diff,
                q_type,
                recent_texts,
            )
            if q_data and q_data.get('question'):
                break
        except Exception as e:
            logger.warning('Generation attempt %d failed: %s', attempt_num + 1, e)
            q_data = None

    if not q_data:
        flask_session['current_question'] = None
        return None

    # Store question in DB
    skill = all_skills.get(focus_node_id, {})
    skill_rating = skill.get('skill_rating', 1000.0)

    question_id = question_model.create(
        curriculum_node_id=focus_node_id,
        content=q_data.get('question', ''),
        question_type=q_type,
        options=json.dumps(q_data.get('options')) if q_data.get('options') else None,
        correct_answer=q_data.get('correct_answer', ''),
        explanation=q_data.get('explanation', ''),
        difficulty=target_diff,
        estimated_p_correct=elo.p_correct(skill_rating, target_diff),
        generated_prompt=prompt,
        model_used=model,
    )

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
    }
    flask_session['current_question'] = question_dict
    return question_dict
