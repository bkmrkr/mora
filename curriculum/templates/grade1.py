"""Grade 1 math question templates — 10 skills.

Each function takes difficulty_elo and returns a dict:
  question, correct_answer, options, explanation, template_id, skill_id
"""
import random

from curriculum.templates.common import (arithmetic_distractors, make_options,
                                        word_problem_frame, estimate_difficulty)


def addition_within_10(difficulty_elo):
    """g1_add_10: Addition with sums up to 10."""
    max_sum = 7 if difficulty_elo < 700 else 10
    a = random.randint(1, max_sum - 1)
    b = random.randint(1, max_sum - a)
    answer = a + b
    distractors = arithmetic_distractors(answer, a, b, op='+')
    return {
        'skill_id': 'g1_add_10',
        'question': f'What is {a} + {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} + {b} = {answer}',
        'template_id': 'g1_add_10',
        'difficulty': estimate_difficulty(1, answer / 10),
    }


def subtraction_within_10(difficulty_elo):
    """g1_sub_10: Subtraction within 10."""
    max_val = 7 if difficulty_elo < 700 else 10
    a = random.randint(2, max_val)
    b = random.randint(1, a - 1)
    answer = a - b
    distractors = arithmetic_distractors(answer, a, b, op='-')
    return {
        'skill_id': 'g1_sub_10',
        'question': f'What is {a} - {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} - {b} = {answer}',
        'template_id': 'g1_sub_10',
        'difficulty': estimate_difficulty(1, a / 10),
    }


def addition_within_20(difficulty_elo):
    """g1_add_20: Addition with sums up to 20."""
    if difficulty_elo < 650:
        max_sum = 15
    elif difficulty_elo < 800:
        max_sum = 18
    else:
        max_sum = 20
    a = random.randint(1, max_sum - 1)
    b = random.randint(1, max_sum - a)
    answer = a + b
    distractors = arithmetic_distractors(answer, a, b, op='+')
    return {
        'skill_id': 'g1_add_20',
        'question': f'What is {a} + {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} + {b} = {answer}',
        'template_id': 'g1_add_20',
        'difficulty': estimate_difficulty(1, answer / 20),
    }


def subtraction_within_20(difficulty_elo):
    """g1_sub_20: Subtraction within 20."""
    max_val = 15 if difficulty_elo < 700 else 20
    a = random.randint(2, max_val)
    b = random.randint(1, a - 1)
    answer = a - b
    distractors = arithmetic_distractors(answer, a, b, op='-')
    return {
        'skill_id': 'g1_sub_20',
        'question': f'What is {a} - {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} - {b} = {answer}',
        'template_id': 'g1_sub_20',
        'difficulty': estimate_difficulty(1, a / 20),
    }


def place_value(difficulty_elo):
    """g1_place_value: Identify tens and ones in 2-digit numbers."""
    num = random.randint(11, 99)
    tens = num // 10
    ones = num % 10

    variants = [
        ('tens', tens, f'How many tens are in {num}?', f'{num} = {tens} tens and {ones} ones'),
        ('ones', ones, f'How many ones are in {num}?', f'{num} = {tens} tens and {ones} ones'),
    ]
    kind, answer, question, explanation = random.choice(variants)

    distractors = arithmetic_distractors(answer, tens, ones)
    return {
        'skill_id': 'g1_place_value',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': f'g1_place_value_{kind}',
        'difficulty': estimate_difficulty(1, num / 99),
    }


def counting_to_120(difficulty_elo):
    """g1_counting: What number comes next/before, count by 2s/5s/10s."""
    if difficulty_elo < 700:
        # Simple: what comes next
        n = random.randint(1, 50)
        return {
            'skill_id': 'g1_counting',
            'question': f'What number comes after {n}?',
            'correct_answer': str(n + 1),
            'options': make_options(str(n + 1), [str(n - 1), str(n), str(n + 2)]),
            'explanation': f'The number after {n} is {n + 1}.',
            'template_id': 'g1_counting_next',
            'difficulty': estimate_difficulty(1, 0.1 + n / 120),
        }
    elif difficulty_elo < 850:
        # What comes before
        n = random.randint(2, 100)
        return {
            'skill_id': 'g1_counting',
            'question': f'What number comes before {n}?',
            'correct_answer': str(n - 1),
            'options': make_options(str(n - 1), [str(n + 1), str(n), str(n - 2)]),
            'explanation': f'The number before {n} is {n - 1}.',
            'template_id': 'g1_counting_before',
            'difficulty': estimate_difficulty(1, 0.3 + n / 200),
        }
    else:
        # Skip counting (keep all numbers within 120)
        skip = random.choice([2, 5, 10])
        max_start = (120 - 3 * skip) // skip * skip  # ensure last number <= 120
        start = random.randint(0, max_start // skip) * skip
        seq = [start + skip * i for i in range(4)]
        answer = seq[-1]
        question = f'Count by {skip}s: {seq[0]}, {seq[1]}, {seq[2]}, ?'
        distractors = [str(answer + skip), str(answer - skip), str(answer + 1)]
        return {
            'skill_id': 'g1_counting',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': f'Counting by {skip}s: the next number is {answer}.',
            'template_id': f'g1_counting_skip_{skip}',
            'difficulty': estimate_difficulty(1, 0.6 + skip / 30),
        }


def comparing_numbers(difficulty_elo):
    """g1_comparing: Which is greater/less, or compare with <, >, =."""
    if difficulty_elo < 750:
        max_val = 50
    else:
        max_val = 120

    a = random.randint(1, max_val)
    b = random.randint(1, max_val)
    while a == b:
        b = random.randint(1, max_val)

    question = f'Which number is greater: {a} or {b}?'
    answer = str(max(a, b))
    wrong = str(min(a, b))
    distractors = [wrong, str(a + b), str(abs(a - b))]
    explanation = f'{max(a, b)} is greater than {min(a, b)}.'

    return {
        'skill_id': 'g1_comparing',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': explanation,
        'template_id': 'g1_comparing',
        'difficulty': estimate_difficulty(1, max(a, b) / 120),
    }


def telling_time_hour(difficulty_elo):
    """g1_time: Tell time to the hour and half-hour (with clock SVG)."""
    if difficulty_elo < 750:
        # Whole hours only
        hour = random.randint(1, 12)
        minute = 0
    else:
        # Include half-hours
        hour = random.randint(1, 12)
        minute = random.choice([0, 30])

    if minute == 0:
        answer = f'{hour}:00'
    else:
        answer = f'{hour}:30'

    # Distractors: wrong hour, wrong minute
    wrong_hours = [h for h in range(1, 13) if h != hour]
    d1_hour = random.choice(wrong_hours)
    d2_hour = random.choice(wrong_hours)
    distractors = [
        f'{d1_hour}:{"00" if minute == 0 else "30"}',
        f'{d2_hour}:{"30" if minute == 0 else "00"}',
        f'{hour}:{"30" if minute == 0 else "00"}',
    ]

    return {
        'skill_id': 'g1_time',
        'question': 'What time does this clock show?',
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'The time is {answer}.',
        'template_id': 'g1_time',
        'difficulty': estimate_difficulty(1, 0.3 if minute == 0 else 0.7),
        'clock_hour': hour,
        'clock_minute': minute,
    }


def basic_shapes(difficulty_elo):
    """g1_shapes: Identify shapes by properties."""
    shapes = [
        ('triangle', 3, 'A triangle has 3 sides and 3 corners.'),
        ('square', 4, 'A square has 4 equal sides and 4 corners.'),
        ('rectangle', 4, 'A rectangle has 4 sides and 4 corners.'),
        ('circle', 0, 'A circle has 0 straight sides — it is round.'),
        ('hexagon', 6, 'A hexagon has 6 sides and 6 corners.'),
    ]

    variant = random.choice(['sides_to_name', 'name_to_sides'])

    if variant == 'sides_to_name':
        # Only use shapes with unique side counts to avoid ambiguity
        # (square and rectangle both have 4 sides)
        unique = [s for s in shapes if s[1] > 0
                  and sum(1 for x in shapes if x[1] == s[1]) == 1]
        name, sides, explanation = random.choice(unique)
        question = f'What shape has {sides} sides?'
        wrong_names = [s[0] for s in shapes if s[0] != name]
        random.shuffle(wrong_names)
        return {
            'skill_id': 'g1_shapes',
            'question': question,
            'correct_answer': name,
            'options': make_options(name, wrong_names[:3]),
            'explanation': explanation,
            'template_id': 'g1_shapes_sides_to_name',
            'difficulty': estimate_difficulty(1, 0.5),
        }
    else:
        name, sides, explanation = random.choice(shapes)
        question = f'How many sides does a {name} have?'
        all_side_counts = list({s[1] for s in shapes if s[1] != sides})
        random.shuffle(all_side_counts)
        distractors = [str(s) for s in all_side_counts[:3]]
        # Pad if needed
        extras = [1, 2, 5, 7, 8]
        for e in extras:
            if len(distractors) >= 3:
                break
            if str(e) not in distractors and e != sides:
                distractors.append(str(e))
        return {
            'skill_id': 'g1_shapes',
            'question': question,
            'correct_answer': str(sides),
            'options': make_options(str(sides), distractors),
            'explanation': explanation,
            'template_id': 'g1_shapes_name_to_sides',
            'difficulty': estimate_difficulty(1, 0.3),
        }


def word_problems_add_sub(difficulty_elo):
    """g1_word_problems: Word problems involving addition and subtraction."""
    op = random.choice(['+', '-'])
    if difficulty_elo < 700:
        max_val = 10
    else:
        max_val = 20

    if op == '+':
        a = random.randint(2, max_val - 1)
        b = random.randint(1, max_val - a)
        answer = a + b
    else:
        a = random.randint(3, max_val)
        b = random.randint(1, a - 1)
        answer = a - b

    question = word_problem_frame(a, b, op, answer)
    distractors = arithmetic_distractors(answer, a, b, op=op)

    return {
        'skill_id': 'g1_word_problems',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} {op} {b} = {answer}',
        'template_id': f'g1_word_problems_{op}',
        'difficulty': estimate_difficulty(1, 0.4 + max(a, b) / 40),
    }


# Registry: skill_id → list of template functions
GRADE1_TEMPLATES = {
    'g1_add_10': [addition_within_10],
    'g1_sub_10': [subtraction_within_10],
    'g1_add_20': [addition_within_20],
    'g1_sub_20': [subtraction_within_20],
    'g1_place_value': [place_value],
    'g1_counting': [counting_to_120],
    'g1_comparing': [comparing_numbers],
    'g1_time': [telling_time_hour],
    'g1_shapes': [basic_shapes],
    'g1_word_problems': [word_problems_add_sub],
}
