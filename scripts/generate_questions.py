#!/usr/bin/env python3
"""Generate questions for all curriculum nodes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.question_generator import generate
from models.question import create as create_question
import json

# All curriculum nodes
CURRICULUM = [
    # Math (topic_id=1)
    (1, 6, 'Kindergarten Math', 'Numbers 1-20, counting, shapes, basic addition', 'Counting'),
    (1, 7, '1st Grade Math', 'Numbers to 100, addition/subtraction to 20', 'Addition'),
    (1, 8, '2nd Grade Math', 'Numbers to 1000, regrouping', 'Place Value'),
    (1, 9, '3rd Grade Math', 'Multiplication, division, fractions', 'Multiplication'),
    (1, 10, '4th Grade Math', 'Multi-digit operations, decimals', 'Multi-digit'),

    # Reading (topic_id=2)
    (2, 11, 'Kindergarten Reading', 'Phonemic awareness, letters, sight words', 'Letters'),
    (2, 12, '1st Grade Reading', 'Phonics, blends, comprehension', 'Phonics'),
    (2, 13, '2nd Grade Reading', 'Vowel teams, cause/effect', 'Comprehension'),
    (2, 14, '3rd Grade Reading', 'Inference, vocabulary', 'Inference'),
    (2, 15, '4th Grade Reading', 'Theme, analysis', 'Analysis'),

    # Science (topic_id=3)
    (3, 16, 'Kindergarten Science', 'Weather, animals, plants, senses', 'Animals'),
    (3, 17, '1st Grade Science', 'Living vs nonliving, life cycles', 'Life Cycles'),
    (3, 18, '2nd Grade Science', 'Habitats, ecosystems, food chains', 'Ecosystems'),
    (3, 19, '3rd Grade Science', 'Forces, magnets, rocks', 'Forces'),
    (3, 20, '4th Grade Science', 'Energy transfer, solar system', 'Solar System'),

    # Social Studies (topic_id=4)
    (4, 21, 'Kindergarten Social Studies', 'Community helpers, citizenship', 'Community'),
    (4, 22, '1st Grade Social Studies', 'Urban/suburban/rural, needs vs wants', 'Communities'),
    (4, 23, '2nd Grade Social Studies', 'Cultures, map skills, government', 'Government'),
    (4, 24, '3rd Grade Social Studies', 'US regions, Constitution', 'History'),
    (4, 25, '4th Grade Social Studies', 'US history, citizenship', 'Citizenship'),

    # Hebrew (topic_id=5)
    (5, 1, 'Kindergarten Hebrew', 'Alef-Bet, basic vocabulary', 'Vocabulary'),
    (5, 2, '1st Grade Hebrew', 'CVC words, Chumash', 'Chumash'),
    (5, 3, '2nd Grade Hebrew', 'Fluency, Rashi', 'Rashi'),
    (5, 4, '3rd Grade Hebrew', 'Chumash, Navi', 'Navi'),
    (5, 5, '4th Grade Hebrew', 'Advanced Hebrew, grammar', 'Grammar'),
]

# Questions per node
QUESTIONS_PER_NODE = 50

def generate_questions():
    total = 0
    errors = 0

    for topic_id, node_id, node_name, desc, skill in CURRICULUM:
        topic_name = {1: 'Math', 2: 'Reading', 3: 'Science', 4: 'Social Studies', 5: 'Hebrew'}[topic_id]

        print(f'\n=== {node_name}: {node_name} ===')

        for i in range(QUESTIONS_PER_NODE):
            try:
                # Vary difficulty per question
                difficulty = 400 + (node_id % 5) * 100 + (i % 50)

                q_data, model, prompt = generate(
                    node_name=node_name,
                    node_description=desc,
                    topic_name=f'{topic_name} (K-4)',
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

                if (i + 1) % 10 == 0:
                    print(f'  {i+1}/{QUESTIONS_PER_NODE} done...')

            except Exception as e:
                errors += 1
                if errors < 5:
                    print(f'  Error: {e}')

        print(f'  Completed {node_name}: {QUESTIONS_PER_NODE} questions')

    print(f'\n=== TOTAL: {total} questions, {errors} errors ===')

if __name__ == '__main__':
    generate_questions()
