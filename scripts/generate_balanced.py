#!/usr/bin/env python3
"""Generate questions for all curriculum nodes - balanced."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.question_generator import generate
from models.question import create as create_question
import json
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mora.db')

def get_current_counts():
    """Get current question counts per node."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("""
        SELECT cn.id, cn.topic_id, COUNT(q.id) as cnt
        FROM curriculum_nodes cn
        LEFT JOIN questions q ON cn.id = q.curriculum_node_id
        GROUP BY cn.id
    """)
    counts = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    conn.close()
    return counts

# Target per node
TARGET = 100

# Curriculum nodes
NODES = [
    # (topic_id, node_id, name, description, skill)
    (1, 6, 'Kindergarten Math', 'Numbers 1-20', 'Counting'),
    (1, 7, '1st Grade Math', 'Numbers to 100', 'Addition'),
    (1, 8, '2nd Grade Math', 'Numbers to 1000', 'Place Value'),
    (1, 9, '3rd Grade Math', 'Multiplication', 'Multiplication'),
    (1, 10, '4th Grade Math', 'Multi-digit', 'Multi-digit'),
    (2, 11, 'Kindergarten Reading', 'Letters', 'Letters'),
    (2, 12, '1st Grade Reading', 'Phonics', 'Phonics'),
    (2, 13, '2nd Grade Reading', 'Comprehension', 'Comprehension'),
    (2, 14, '3rd Grade Reading', 'Inference', 'Inference'),
    (2, 15, '4th Grade Reading', 'Analysis', 'Analysis'),
    (3, 16, 'Kindergarten Science', 'Animals', 'Animals'),
    (3, 17, '1st Grade Science', 'Life Cycles', 'Life Cycles'),
    (3, 18, '2nd Grade Science', 'Ecosystems', 'Ecosystems'),
    (3, 19, '3rd Grade Science', 'Forces', 'Forces'),
    (3, 20, '4th Grade Science', 'Solar System', 'Solar System'),
    (4, 21, 'Kindergarten Social Studies', 'Community', 'Community'),
    (4, 22, '1st Grade Social Studies', 'Communities', 'Communities'),
    (4, 23, '2nd Grade Social Studies', 'Government', 'Government'),
    (4, 24, '3rd Grade Social Studies', 'History', 'History'),
    (4, 25, '4th Grade Social Studies', 'Citizenship', 'Citizenship'),
    (5, 1, 'Kindergarten Hebrew', 'Vocabulary', 'Vocabulary'),
    (5, 2, '1st Grade Hebrew', 'Chumash', 'Chumash'),
    (5, 3, '2nd Grade Hebrew', 'Rashi', 'Rashi'),
    (5, 4, '3rd Grade Hebrew', 'Navi', 'Navi'),
    (5, 5, '4th Grade Hebrew', 'Grammar', 'Grammar'),
]

TOPIC_NAMES = {1: 'Math', 2: 'Reading', 3: 'Science', 4: 'Social Studies', 5: 'Hebrew'}

def generate_questions():
    total = 0
    errors = 0

    while True:
        counts = get_current_counts()

        # Find nodes that need more questions
        needs_more = []
        for topic_id, node_id, node_name, desc, skill in NODES:
            current = counts.get(node_id, (0, 0))[1] if isinstance(counts.get(node_id), tuple) else 0
            if current < TARGET:
                needs_more.append((topic_id, node_id, node_name, desc, skill, current))

        if not needs_more:
            print("All nodes have reached target!")
            break

        # Generate for nodes that need questions
        for topic_id, node_id, node_name, desc, skill, current in needs_more:
            topic = TOPIC_NAMES[topic_id]
            difficulty = 400 + (node_id % 5) * 100

            try:
                q_data, model, prompt = generate(
                    node_name=node_name,
                    node_description=desc,
                    topic_name=f'{topic} (K-4)',
                    target_difficulty_elo=difficulty,
                    question_type='mcq'
                )

                create_question(
                    curriculum_node_id=node_id,
                    content=q_data.get('question', ''),
                    question_type='mcq',
                    options=json.dumps(q_data.get('options', [])),
                    correct_answer=q_data.get('correct_answer', ''),
                    explanation=q_data.get('explanation', ''),
                    difficulty=difficulty,
                    generated_prompt=prompt,
                    model_used=model
                )
                total += 1
                print(f'{node_name}: {current+1}/{TARGET}')

            except Exception as e:
                errors += 1
                if errors < 10:
                    print(f'Error {node_name}: {e}')

        # Check total
        total_now = sum(c[1] for c in get_current_counts().values())
        print(f'\n=== Total: {total_now} questions ===\n')

        if total_now >= 2500:
            break

if __name__ == '__main__':
    generate_questions()
