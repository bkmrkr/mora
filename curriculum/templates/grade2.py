"""Grade 2 math question templates — 10 skills.

Each function takes difficulty_elo and returns a dict:
  question, correct_answer, options, explanation, template_id, skill_id
"""
import random

from curriculum.templates.common import arithmetic_distractors, make_options, word_problem_frame


def add_sub_within_100(difficulty_elo):
    """g2_add_sub_100: Add/sub with regrouping within 100."""
    op = random.choice(['+', '-'])
    if difficulty_elo < 700:
        max_val = 50
    else:
        max_val = 99

    if op == '+':
        a = random.randint(10, max_val - 10)
        b = random.randint(10, max_val - a)
        answer = a + b
    else:
        a = random.randint(20, max_val)
        b = random.randint(10, a - 1)
        answer = a - b

    distractors = arithmetic_distractors(answer, a, b, op=op)
    return {
        'skill_id': 'g2_add_sub_100',
        'question': f'What is {a} {op} {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} {op} {b} = {answer}',
        'template_id': f'g2_add_sub_100_{op}',
    }


def add_sub_within_1000(difficulty_elo):
    """g2_add_sub_1000: Add/sub within 1000."""
    op = random.choice(['+', '-'])
    if difficulty_elo < 750:
        max_val = 500
    else:
        max_val = 999

    if op == '+':
        a = random.randint(100, max_val - 100)
        b = random.randint(50, max_val - a)
        answer = a + b
    else:
        a = random.randint(200, max_val)
        b = random.randint(50, a - 1)
        answer = a - b

    distractors = arithmetic_distractors(answer, a, b, op=op)
    return {
        'skill_id': 'g2_add_sub_1000',
        'question': f'What is {a} {op} {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} {op} {b} = {answer}',
        'template_id': f'g2_add_sub_1000_{op}',
    }


def intro_multiply(difficulty_elo):
    """g2_intro_multiply: Equal groups multiplication intro."""
    if difficulty_elo < 700:
        groups = random.randint(2, 5)
        per_group = random.randint(2, 5)
    else:
        groups = random.randint(2, 10)
        per_group = random.randint(2, 6)

    answer = groups * per_group
    items = random.choice(['apples', 'stickers', 'stars', 'marbles', 'cookies'])

    question = f'There are {groups} bags with {per_group} {items} in each bag. How many {items} in all?'
    distractors = arithmetic_distractors(answer, groups, per_group, op='*')
    return {
        'skill_id': 'g2_intro_multiply',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{groups} groups of {per_group} = {groups} x {per_group} = {answer}',
        'template_id': 'g2_intro_multiply',
    }


def money(difficulty_elo):
    """g2_money: Coins and making change."""
    coins = {'quarter': 25, 'dime': 10, 'nickel': 5, 'penny': 1}

    if difficulty_elo < 750:
        # Count coin values
        coin_name, coin_val = random.choice(list(coins.items()))
        count = random.randint(2, 6)
        answer = count * coin_val
        question = f'How many cents are {count} {coin_name}s worth?'
        explanation = f'{count} {coin_name}s = {count} x {coin_val} = {answer} cents'
    else:
        # Mixed coins
        q = random.randint(0, 3)
        d = random.randint(0, 5)
        n = random.randint(0, 4)
        p = random.randint(0, 4)
        answer = q * 25 + d * 10 + n * 5 + p * 1
        if answer == 0:
            q, d = 1, 1
            answer = 35
        parts = []
        if q: parts.append(f'{q} quarter{"s" if q > 1 else ""}')
        if d: parts.append(f'{d} dime{"s" if d > 1 else ""}')
        if n: parts.append(f'{n} nickel{"s" if n > 1 else ""}')
        if p: parts.append(f'{p} penn{"ies" if p > 1 else "y"}')
        question = f'How many cents is {", ".join(parts)} worth?'
        explanation = f'{" + ".join(parts)} = {answer} cents'

    distractors = [str(answer + 5), str(answer - 5), str(answer + 10)]
    distractors = [d for d in distractors if int(d) > 0]
    return {
        'skill_id': 'g2_money',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': 'g2_money',
    }


def telling_time_5min(difficulty_elo):
    """g2_time: Tell time to the nearest 5 minutes."""
    hour = random.randint(1, 12)
    minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    answer = f'{hour}:{minute:02d}'

    wrong_hours = [h for h in range(1, 13) if h != hour]
    d1_h = random.choice(wrong_hours)
    d2_min = (minute + 5) % 60
    d3_min = (minute - 5) % 60

    distractors = [
        f'{d1_h}:{minute:02d}',
        f'{hour}:{d2_min:02d}',
        f'{hour}:{d3_min:02d}',
    ]

    question = f'A clock shows {hour} hour{"s" if hour > 1 else ""} and {minute} minutes. What time is it?'
    return {
        'skill_id': 'g2_time',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'The time is {answer}.',
        'template_id': 'g2_time',
    }


def measurement_length(difficulty_elo):
    """g2_measurement: Measuring and comparing lengths."""
    if difficulty_elo < 750:
        # Simple comparison
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        while a == b:
            b = random.randint(1, 20)
        unit = random.choice(['inches', 'centimeters'])
        question = f'A pencil is {a} {unit} long and a crayon is {b} {unit} long. Which is longer?'
        answer = 'pencil' if a > b else 'crayon'
        wrong = 'crayon' if a > b else 'pencil'
        explanation = f'{max(a, b)} {unit} > {min(a, b)} {unit}, so the {answer} is longer.'
        return {
            'skill_id': 'g2_measurement',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, [wrong, 'both the same', 'cannot tell']),
            'explanation': explanation,
            'template_id': 'g2_measurement_compare',
        }
    else:
        # Addition of lengths
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        answer = a + b
        unit = random.choice(['inches', 'centimeters'])
        question = f'A rope is {a} {unit} long. Another rope is {b} {unit} long. How long are they together?'
        distractors = arithmetic_distractors(answer, a, b, op='+')
        return {
            'skill_id': 'g2_measurement',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': f'{a} + {b} = {answer} {unit}',
            'template_id': 'g2_measurement_add',
        }


def fractions_intro(difficulty_elo):
    """g2_fractions_intro: Identify halves, thirds, fourths."""
    fractions = [
        (1, 2, 'half', 'halves'),
        (1, 3, 'one third', 'thirds'),
        (2, 3, 'two thirds', 'thirds'),
        (1, 4, 'one fourth', 'fourths'),
        (2, 4, 'two fourths', 'fourths'),
        (3, 4, 'three fourths', 'fourths'),
    ]
    num, den, name, _ = random.choice(fractions)
    whole = random.randint(6, 24)
    # Make sure whole divides evenly
    whole = whole // den * den
    answer = whole * num // den

    question = f'What is {name} of {whole}?'
    distractors = arithmetic_distractors(answer, whole, den, op='/')
    return {
        'skill_id': 'g2_fractions_intro',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{name} of {whole} = {whole} ÷ {den} × {num} = {answer}',
        'template_id': 'g2_fractions_intro',
    }


def comparing_3digit(difficulty_elo):
    """g2_comparing_3digit: Compare 3-digit numbers."""
    a = random.randint(100, 999)
    b = random.randint(100, 999)
    while a == b:
        b = random.randint(100, 999)

    question = f'Which number is greater: {a} or {b}?'
    answer = str(max(a, b))
    wrong = str(min(a, b))
    distractors = [wrong, str(a + b), str(abs(a - b))]

    return {
        'skill_id': 'g2_comparing_3digit',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'{max(a, b)} > {min(a, b)}',
        'template_id': 'g2_comparing_3digit',
    }


def two_step_word(difficulty_elo):
    """g2_two_step: Two-step word problems."""
    a = random.randint(5, 30)
    b = random.randint(3, 15)
    c = random.randint(2, 10)

    variant = random.choice(['add_then_sub', 'add_then_add', 'sub_then_add'])
    if variant == 'add_then_sub':
        answer = a + b - c
        question = f'Sam has {a} stickers. He gets {b} more, then gives away {c}. How many stickers does Sam have?'
        explanation = f'{a} + {b} = {a + b}, then {a + b} - {c} = {answer}'
    elif variant == 'add_then_add':
        answer = a + b + c
        question = f'A store has {a} red balls, {b} blue balls, and {c} green balls. How many balls in total?'
        explanation = f'{a} + {b} + {c} = {answer}'
    else:
        a = max(a, b + c)  # ensure non-negative
        answer = a - b + c
        question = f'There are {a} birds in a tree. {b} fly away, then {c} more land. How many birds are there?'
        explanation = f'{a} - {b} = {a - b}, then {a - b} + {c} = {answer}'

    distractors = arithmetic_distractors(answer, a, b)
    return {
        'skill_id': 'g2_two_step',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': f'g2_two_step_{variant}',
    }


def odd_even(difficulty_elo):
    """g2_odd_even: Identify odd and even numbers."""
    if difficulty_elo < 750:
        n = random.randint(1, 50)
        correct = 'even' if n % 2 == 0 else 'odd'
        question = f'Is {n} odd or even?'
        return {
            'skill_id': 'g2_odd_even',
            'question': question,
            'correct_answer': correct,
            'options': make_options(correct, ['odd' if correct == 'even' else 'even',
                                              'neither', 'both']),
            'explanation': f'{n} is {correct} because {n} ÷ 2 = {n / 2}.',
            'template_id': 'g2_odd_even_identify',
        }
    else:
        numbers = random.sample(range(1, 40), 4)
        target = random.choice(['even', 'odd'])
        # Ensure at least one correct answer
        matching = [n for n in numbers if (n % 2 == 0) == (target == 'even')]
        if not matching:
            numbers[0] = numbers[0] + 1 if target == 'even' and numbers[0] % 2 != 0 else numbers[0]
            if target == 'even' and numbers[0] % 2 != 0:
                numbers[0] += 1
            elif target == 'odd' and numbers[0] % 2 == 0:
                numbers[0] += 1
            matching = [n for n in numbers if (n % 2 == 0) == (target == 'even')]

        answer = str(matching[0])
        wrong = [str(n) for n in numbers if str(n) != answer]
        question = f'Which of these numbers is {target}?'
        return {
            'skill_id': 'g2_odd_even',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, wrong[:3]),
            'explanation': f'{answer} is {target}.',
            'template_id': 'g2_odd_even_which',
        }


GRADE2_TEMPLATES = {
    'g2_add_sub_100': [add_sub_within_100],
    'g2_add_sub_1000': [add_sub_within_1000],
    'g2_intro_multiply': [intro_multiply],
    'g2_money': [money],
    'g2_time': [telling_time_5min],
    'g2_measurement': [measurement_length],
    'g2_fractions_intro': [fractions_intro],
    'g2_comparing_3digit': [comparing_3digit],
    'g2_two_step': [two_step_word],
    'g2_odd_even': [odd_even],
}
