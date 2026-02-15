"""Question generator testing script.

Usage:
    python -m scripts.question_tester [--limit N] [--node-id ID] [--topic-id ID]

This script:
1. Generates questions for curriculum nodes
2. Validates them using the question_validator
3. Stores them in DB with test_status='pending_review'
4. Provides an admin interface to review and approve questions
"""
import argparse
import json
import logging
import os
import sys
import time
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db, execute_db, query_db
from models.curriculum_node import get_by_id, get_for_topic
from models.topic import get_all, get_by_id as get_topic_by_id
from models.question import create as create_question, get_by_id as get_question_by_id
from ai.question_generator import generate as generate_question
from ai.local_generators import (is_clock_node, generate_clock_question,
                                 is_inequality_node, generate_inequality_question)
from engine.question_validator import validate_question

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def get_nodes_without_questions(topic_id=None, limit=5):
    """Get curriculum nodes that don't have questions yet."""
    conn = get_db()
    try:
        if topic_id:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                WHERE cn.topic_id = ?
                AND NOT EXISTS (
                    SELECT 1 FROM questions q
                    WHERE q.curriculum_node_id = cn.id
                )
                ORDER BY cn.order_index
                LIMIT ?
            """, (topic_id, limit))
        else:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                WHERE NOT EXISTS (
                    SELECT 1 FROM questions q
                    WHERE q.curriculum_node_id = cn.id
                )
                ORDER BY cn.order_index
                LIMIT ?
            """, (limit,))
        return nodes
    finally:
        conn.close()


def get_all_nodes(limit=None):
    """Get all curriculum nodes."""
    conn = get_db()
    try:
        if limit:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                ORDER BY cn.order_index
                LIMIT ?
            """, (limit,))
        else:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                ORDER BY cn.order_index
            """)
        return nodes
    finally:
        conn.close()


def get_nodes_need_more_questions(topic_id=None, min_questions=3, limit=5):
    """Get nodes that need more questions."""
    conn = get_db()
    try:
        if topic_id:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name,
                       (SELECT COUNT(*) FROM questions q WHERE q.curriculum_node_id = cn.id) as q_count
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                WHERE cn.topic_id = ?
                AND (SELECT COUNT(*) FROM questions q WHERE q.curriculum_node_id = cn.id) < ?
                ORDER BY q_count ASC, cn.order_index
                LIMIT ?
            """, (topic_id, min_questions, limit))
        else:
            nodes = query_db("""
                SELECT cn.*, t.name as topic_name,
                       (SELECT COUNT(*) FROM questions q WHERE q.curriculum_node_id = cn.id) as q_count
                FROM curriculum_nodes cn
                JOIN topics t ON cn.topic_id = t.id
                WHERE (SELECT COUNT(*) FROM questions q WHERE q.curriculum_node_id = cn.id) < ?
                ORDER BY q_count ASC, cn.order_index
                LIMIT ?
            """, (min_questions, limit))
        return nodes
    finally:
        conn.close()


def save_question_for_testing(node, q_data, model_used, prompt_used):
    """Save a question with test_status='pending_review'."""
    conn = get_db()
    try:
        # Handle options (may be None or a list)
        options_json = json.dumps(q_data.get('options') or [])

        cursor = conn.execute("""
            INSERT INTO questions
            (curriculum_node_id, content, question_type, options, correct_answer,
             explanation, difficulty, estimated_p_correct, generated_prompt, model_used,
             quality_flags, test_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending_review')
        """, (
            node['id'],
            q_data.get('question', ''),
            q_data.get('question_type', 'mcq'),
            options_json,
            q_data.get('correct_answer', ''),
            q_data.get('explanation', ''),
            q_data.get('difficulty'),
            q_data.get('estimated_p_correct'),
            prompt_used,
            model_used,
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def generate_and_test_question(node, target_difficulty=800, max_retries=3):
    """Generate a question and validate it.

    Returns (question_id, is_valid, validation_message, q_data)
    """
    node_name = node['name']
    node_desc = node.get('description', '')
    topic_name = node.get('topic_name', '')

    for attempt in range(max_retries):
        try:
            # Try local generators first (clock, inequality)
            q_data = None
            model_used = None
            prompt_used = None

            if is_clock_node(node_name, node_desc):
                q_data, model_used, prompt_used = generate_clock_question(node_name, node_desc)
                if q_data:
                    q_data['_model_used'] = 'local_generator'
                    q_data['_prompt_used'] = 'local_generator'
            elif is_inequality_node(node_name, node_desc):
                q_data, model_used, prompt_used = generate_inequality_question(node_name, node_desc)
                if q_data:
                    q_data['_model_used'] = 'local_generator'
                    q_data['_prompt_used'] = 'local_generator'

            if not q_data:
                # Use LLM generator
                q_data, model_used, prompt_used = generate_question(
                    node_name=node_name,
                    node_description=node_desc,
                    topic_name=topic_name,
                    target_difficulty_elo=target_difficulty,
                    question_type='mcq',
                    recent_questions=None
                )
                q_data['_model_used'] = model_used
                q_data['_prompt_used'] = prompt_used

            # Validate the question
            is_valid, reason = validate_question(q_data, node_desc)

            if is_valid:
                return None, True, '', q_data
            else:
                logger.warning(f"Validation failed for {node_name}: {reason}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying ({attempt + 2}/{max_retries})...")
                    time.sleep(1)
                    continue
                return None, False, reason, q_data

        except Exception as e:
            logger.error(f"Error generating question for {node_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, False, str(e), None

    return None, False, 'Max retries exceeded', None


def run_test_loop(topic_id=None, limit=None, questions_per_node=3, run_forever=False):
    """Run the question testing loop.

    Args:
        topic_id: Filter by specific topic
        limit: Maximum nodes to process (None = all)
        questions_per_node: How many questions to generate per node
        run_forever: If True, loop indefinitely
    """
    logger.info("Starting question generator testing loop")
    logger.info(f"Topic ID: {topic_id}, Limit: {limit}, Questions per node: {questions_per_node}")

    iteration = 0
    stats = {'generated': 0, 'valid': 0, 'invalid': 0, 'errors': 0}

    while True:
        iteration += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Iteration {iteration}")
        logger.info(f"Stats: {stats}")
        logger.info(f"{'='*60}")

        # Get nodes that need questions
        nodes = get_nodes_without_questions(topic_id=topic_id, limit=limit)

        if not nodes:
            # Try nodes that need more questions
            nodes = get_nodes_need_more_questions(
                topic_id=topic_id,
                min_questions=questions_per_node,
                limit=limit or 10
            )

        if not nodes:
            if run_forever:
                logger.info("All nodes have questions. Waiting 60 seconds...")
                time.sleep(60)
                continue
            else:
                logger.info("All nodes have questions!")
                break

        # Shuffle for variety
        random.shuffle(nodes)

        for node in nodes:
            node_name = node['name']
            node_id = node['id']
            logger.info(f"\nProcessing node: {node_name} (ID: {node_id})")

            # Generate target difficulty (vary it for diversity)
            target_difficulty = random.randint(500, 1000)

            question_id, is_valid, reason, q_data = generate_and_test_question(
                node,
                target_difficulty=target_difficulty
            )

            if is_valid and q_data:
                # Save for testing
                qid = save_question_for_testing(
                    node, q_data,
                    q_data.get('_model_used', 'unknown'),
                    q_data.get('_prompt_used', '')
                )
                logger.info(f"✓ Saved question ID {qid} for review")
                stats['generated'] += 1
                stats['valid'] += 1

                # Try to generate more questions at different difficulties
                for extra in range(questions_per_node - 1):
                    target_difficulty = random.randint(400, 1100)
                    question_id, is_valid, reason, q_data = generate_and_test_question(
                        node,
                        target_difficulty=target_difficulty
                    )
                    if is_valid and q_data:
                        qid = save_question_for_testing(
                            node, q_data,
                            q_data.get('_model_used', 'unknown'),
                            q_data.get('_prompt_used', '')
                        )
                        logger.info(f"✓ Saved extra question ID {qid} for review")
                        stats['generated'] += 1
                        stats['valid'] += 1
                    else:
                        logger.warning(f"✗ Extra question failed: {reason}")
                        stats['invalid'] += 1

            else:
                logger.warning(f"✗ Question failed: {reason}")
                stats['invalid'] += 1

                # Save failed attempt for analysis
                if q_data:
                    conn = get_db()
                    try:
                        options_json = json.dumps(q_data.get('options') or [])
                        conn.execute("""
                            INSERT INTO questions
                            (curriculum_node_id, content, question_type, options, correct_answer,
                             explanation, test_status, validation_error, quality_flags)
                            VALUES (?, ?, ?, ?, ?, ?, 'rejected', ?, 0)
                        """, (
                            node['id'],
                            q_data.get('question', ''),
                            q_data.get('question_type', 'mcq'),
                            options_json,
                            q_data.get('correct_answer', ''),
                            q_data.get('explanation', ''),
                            reason
                        ))
                        conn.commit()
                    finally:
                        conn.close()

            # Small delay between questions
            time.sleep(0.5)

        if not run_forever:
            break

    logger.info(f"\n{'='*60}")
    logger.info(f"Final stats: {stats}")
    logger.info(f"{'='*60}")
    return stats


def main():
    parser = argparse.ArgumentParser(description='Question generator testing loop')
    parser.add_argument('--topic-id', type=int, help='Filter by topic ID')
    parser.add_argument('--node-id', type=int, help='Generate for specific node ID')
    parser.add_argument('--limit', type=int, default=10, help='Max nodes to process')
    parser.add_argument('--questions-per-node', type=int, default=3,
                       help='Questions to generate per node')
    parser.add_argument('--forever', action='store_true',
                       help='Run indefinitely')

    args = parser.parse_args()

    if args.node_id:
        # Generate for specific node
        node = get_by_id(args.node_id)
        if not node:
            logger.error(f"Node {args.node_id} not found")
            return

        topic = get_topic_by_id(node['topic_id'])
        node['topic_name'] = topic['name'] if topic else ''

        logger.info(f"Generating for node: {node['name']}")
        question_id, is_valid, reason, q_data = generate_and_test_question(node)

        if is_valid and q_data:
            qid = save_question_for_testing(
                node, q_data,
                q_data.get('_model_used', 'unknown'),
                q_data.get('_prompt_used', '')
            )
            logger.info(f"✓ Saved question ID {qid} for review")
        else:
            logger.warning(f"✗ Question failed: {reason}")
    else:
        run_test_loop(
            topic_id=args.topic_id,
            limit=args.limit,
            questions_per_node=args.questions_per_node,
            run_forever=args.forever
        )


if __name__ == '__main__':
    main()
