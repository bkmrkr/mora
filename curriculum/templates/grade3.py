"""Grade 3 math question templates — 10 skills.

Each function takes difficulty_elo and returns a dict:
  question, correct_answer, options, explanation, template_id, skill_id
"""
import random

from curriculum.templates.common import arithmetic_distractors, make_options, estimate_difficulty


def multiplication_facts(difficulty_elo):
    """g3_mult_facts: Multiplication facts 0-12."""
    if difficulty_elo < 700:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
    elif difficulty_elo < 850:
        a = random.randint(2, 9)
        b = random.randint(2, 9)
    else:
        a = random.randint(2, 12)
        b = random.randint(2, 12)

    answer = a * b
    distractors = arithmetic_distractors(answer, a, b, op='*')
    return {
        'skill_id': 'g3_mult_facts',
        'question': f'What is {a} × {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} × {b} = {answer}',
        'template_id': 'g3_mult_facts',
        'difficulty': estimate_difficulty(3, min(answer / 144, 1.0)),
    }


def division_facts(difficulty_elo):
    """g3_div_facts: Division facts 0-12."""
    if difficulty_elo < 700:
        divisor = random.randint(2, 5)
        quotient = random.randint(1, 5)
    elif difficulty_elo < 850:
        divisor = random.randint(2, 9)
        quotient = random.randint(1, 9)
    else:
        divisor = random.randint(2, 12)
        quotient = random.randint(1, 12)

    dividend = divisor * quotient
    answer = quotient
    distractors = arithmetic_distractors(answer, dividend, divisor, op='/')
    return {
        'skill_id': 'g3_div_facts',
        'question': f'What is {dividend} ÷ {divisor}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{dividend} ÷ {divisor} = {answer}',
        'template_id': 'g3_div_facts',
        'difficulty': estimate_difficulty(3, min(dividend / 144, 1.0)),
    }


def multi_digit_multiply(difficulty_elo):
    """g3_multi_digit_mult: 2-digit × 1-digit multiplication."""
    if difficulty_elo < 750:
        a = random.randint(10, 30)
        b = random.randint(2, 5)
    else:
        a = random.randint(10, 99)
        b = random.randint(2, 9)

    answer = a * b
    distractors = arithmetic_distractors(answer, a, b, op='*')
    return {
        'skill_id': 'g3_multi_digit_mult',
        'question': f'What is {a} × {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} × {b} = {answer}',
        'template_id': 'g3_multi_digit_mult',
        'difficulty': estimate_difficulty(3, min(answer / 891, 1.0)),
    }


def area_perimeter(difficulty_elo):
    """g3_area_perimeter: Area and perimeter of rectangles."""
    variant = random.choice(['area', 'perimeter'])
    if difficulty_elo < 750:
        length = random.randint(2, 8)
        width = random.randint(2, 8)
    else:
        length = random.randint(3, 15)
        width = random.randint(2, 12)

    if variant == 'area':
        answer = length * width
        question = f'What is the area of a rectangle with length {length} and width {width}?'
        explanation = f'Area = length × width = {length} × {width} = {answer}'
        distractors = [str(2 * (length + width)),  # perimeter mistake
                       str(answer + length), str(answer - width)]
    else:
        answer = 2 * (length + width)
        question = f'What is the perimeter of a rectangle with length {length} and width {width}?'
        explanation = f'Perimeter = 2 × (length + width) = 2 × ({length} + {width}) = {answer}'
        distractors = [str(length * width),  # area mistake
                       str(answer + 2), str(answer - 2)]

    distractors = [d for d in distractors if int(d) > 0 and d != str(answer)]
    return {
        'skill_id': 'g3_area_perimeter',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': f'g3_area_perimeter_{variant}',
        'difficulty': estimate_difficulty(3, 0.3 + (length * width) / 180),
    }


def fraction_compare(difficulty_elo):
    """g3_fraction_compare: Compare fractions and find equivalents."""
    if difficulty_elo < 750:
        # Same denominator comparison
        den = random.choice([3, 4, 5, 6, 8])
        a = random.randint(1, den - 1)
        b = random.randint(1, den - 1)
        while a == b:
            b = random.randint(1, den - 1)
        question = f'Which is greater: {a}/{den} or {b}/{den}?'
        answer = f'{max(a, b)}/{den}'
        wrong = f'{min(a, b)}/{den}'
        explanation = f'{max(a, b)}/{den} > {min(a, b)}/{den} because {max(a, b)} > {min(a, b)}'
        return {
            'skill_id': 'g3_fraction_compare',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, [wrong, 'they are equal',
                                             f'{den}/{max(a, b)}']),
            'explanation': explanation,
            'template_id': 'g3_fraction_compare_same_den',
            'difficulty': estimate_difficulty(3, 0.3),
        }
    else:
        # Different denominator comparison (unit fractions)
        dens = random.sample([2, 3, 4, 5, 6, 8, 10], 2)
        a_den, b_den = dens
        question = f'Which is greater: 1/{a_den} or 1/{b_den}?'
        answer = f'1/{min(a_den, b_den)}'
        wrong = f'1/{max(a_den, b_den)}'
        explanation = f'1/{min(a_den, b_den)} > 1/{max(a_den, b_den)} because smaller denominator means bigger piece'
        return {
            'skill_id': 'g3_fraction_compare',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, [wrong, 'they are equal',
                                             f'1/{a_den + b_den}']),
            'explanation': explanation,
            'template_id': 'g3_fraction_compare_unit',
            'difficulty': estimate_difficulty(3, 0.6 + max(a_den, b_den) / 20),
        }


def fraction_add_sub(difficulty_elo):
    """g3_fraction_add_sub: Add/sub fractions with same denominator."""
    den = random.choice([3, 4, 5, 6, 8])
    op = random.choice(['+', '-'])

    if op == '+':
        a = random.randint(1, den - 2)
        b = random.randint(1, den - a)
        answer_num = a + b
    else:
        a = random.randint(2, den - 1)
        b = random.randint(1, a - 1)
        answer_num = a - b

    question = f'What is {a}/{den} {op} {b}/{den}?'
    answer = f'{answer_num}/{den}'
    # Common mistakes: wrong operation, add denominators
    wrong1 = f'{a + b if op == "-" else abs(a - b)}/{den}'
    wrong2 = f'{answer_num}/{den * 2}'
    wrong3 = f'{answer_num + 1}/{den}'
    distractors = [d for d in [wrong1, wrong2, wrong3] if d != answer]

    return {
        'skill_id': 'g3_fraction_add_sub',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'{a}/{den} {op} {b}/{den} = {answer_num}/{den}',
        'template_id': f'g3_fraction_add_sub_{op}',
        'difficulty': estimate_difficulty(3, 0.4 + den / 16),
    }


def rounding(difficulty_elo):
    """g3_rounding: Round to nearest 10 or 100."""
    if difficulty_elo < 750:
        # Round to nearest 10
        n = random.randint(11, 99)
        target = 10
        answer = round(n / 10) * 10
        question = f'Round {n} to the nearest ten.'
    else:
        # Round to nearest 100
        n = random.randint(101, 999)
        target = 100
        answer = round(n / 100) * 100
        question = f'Round {n} to the nearest hundred.'

    # Distractors: round in wrong direction, nearby multiples
    if target == 10:
        distractors = [
            str(answer + 10), str(answer - 10),
            str(n // 10 * 10 if answer != n // 10 * 10 else answer + 10),
        ]
    else:
        distractors = [
            str(answer + 100), str(answer - 100),
            str(n // 100 * 100 if answer != n // 100 * 100 else answer + 100),
        ]
    distractors = [d for d in distractors if int(d) >= 0 and d != str(answer)]

    return {
        'skill_id': 'g3_rounding',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{n} rounded to the nearest {target} is {answer}.',
        'template_id': f'g3_rounding_{target}',
        'difficulty': estimate_difficulty(3, 0.2 if target == 10 else 0.6),
    }


def mult_div_word_problems(difficulty_elo):
    """g3_mult_div_word: Multiplication and division word problems."""
    op = random.choice(['*', '/'])

    if op == '*':
        a = random.randint(2, 10)
        b = random.randint(2, 8)
        answer = a * b
        templates = [
            f'There are {a} rows with {b} chairs in each row. How many chairs in total?',
            f'A pack of cards has {b} cards. How many cards are in {a} packs?',
            f'{a} children each have {b} crayons. How many crayons in all?',
        ]
        question = random.choice(templates)
        explanation = f'{a} × {b} = {answer}'
        distractors = arithmetic_distractors(answer, a, b, op='*')
    else:
        divisor = random.randint(2, 8)
        quotient = random.randint(2, 8)
        dividend = divisor * quotient
        answer = quotient
        templates = [
            f'{dividend} cookies are shared equally among {divisor} friends. How many does each friend get?',
            f'A teacher puts {dividend} pencils into groups of {divisor}. How many groups are there?',
            f'{dividend} flowers are put into {divisor} vases equally. How many flowers in each vase?',
        ]
        question = random.choice(templates)
        explanation = f'{dividend} ÷ {divisor} = {answer}'
        distractors = arithmetic_distractors(answer, dividend, divisor, op='/')

    return {
        'skill_id': 'g3_mult_div_word',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': f'g3_mult_div_word_{op}',
        'difficulty': estimate_difficulty(3, 0.3 + answer / 80),
    }


def elapsed_time(difficulty_elo):
    """g3_elapsed_time: Calculate elapsed time."""
    if difficulty_elo < 750:
        # Whole hour differences
        start_h = random.randint(1, 10)
        diff_h = random.randint(1, 4)
        end_h = start_h + diff_h
        if end_h > 12:
            end_h -= 12
        answer = diff_h
        question = f'A movie starts at {start_h}:00 and ends at {end_h}:00. How many hours long is the movie?'
        distractors = [str(diff_h + 1), str(diff_h - 1) if diff_h > 1 else '0',
                       str(diff_h + 2)]
    else:
        # Half-hour or minute differences
        start_h = random.randint(1, 10)
        start_m = random.choice([0, 15, 30])
        diff_m = random.choice([30, 45, 60, 90, 120])
        total_start = start_h * 60 + start_m
        total_end = total_start + diff_m
        end_h = (total_end // 60) % 12 or 12
        end_m = total_end % 60

        if diff_m >= 60:
            answer_h = diff_m // 60
            answer_m = diff_m % 60
            if answer_m == 0:
                answer = f'{answer_h} hour{"s" if answer_h > 1 else ""}'
            else:
                answer = f'{answer_h} hour{"s" if answer_h > 1 else ""} {answer_m} minutes'
        else:
            answer = f'{diff_m} minutes'

        question = f'Class starts at {start_h}:{start_m:02d} and ends at {end_h}:{end_m:02d}. How long is class?'
        distractors = [f'{diff_m + 30} minutes', f'{diff_m - 15} minutes',
                       f'{diff_m + 15} minutes']

    return {
        'skill_id': 'g3_elapsed_time',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'The elapsed time is {answer}.',
        'template_id': 'g3_elapsed_time',
        'difficulty': estimate_difficulty(3, 0.3 if isinstance(answer, int) else 0.7),
    }


def data_interpretation(difficulty_elo):
    """g3_data: Read and interpret data from tables/bar graphs (described)."""
    items = random.sample(['cats', 'dogs', 'birds', 'fish', 'hamsters'], 4)
    values = random.sample(range(2, 16), 4)  # Unique values to avoid ties

    variant = random.choice(['most', 'total', 'difference', 'fewest'])

    table_desc = ', '.join(f'{items[i]}: {values[i]}' for i in range(4))

    if variant == 'most':
        max_idx = values.index(max(values))
        answer = items[max_idx]
        question = f'A class survey shows: {table_desc}. Which pet is the most popular?'
        wrong = [items[i] for i in range(4) if i != max_idx]
        explanation = f'{items[max_idx]} has the most with {values[max_idx]}.'
        return {
            'skill_id': 'g3_data',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, wrong[:3]),
            'explanation': explanation,
            'template_id': 'g3_data_most',
            'difficulty': estimate_difficulty(3, 0.2),
        }
    elif variant == 'fewest':
        min_idx = values.index(min(values))
        answer = items[min_idx]
        question = f'A class survey shows: {table_desc}. Which pet is the least popular?'
        wrong = [items[i] for i in range(4) if i != min_idx]
        explanation = f'{items[min_idx]} has the fewest with {values[min_idx]}.'
        return {
            'skill_id': 'g3_data',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, wrong[:3]),
            'explanation': explanation,
            'template_id': 'g3_data_fewest',
            'difficulty': estimate_difficulty(3, 0.2),
        }
    elif variant == 'total':
        answer = sum(values)
        question = f'A class survey shows: {table_desc}. How many pets in total?'
        distractors = [str(answer + 3), str(answer - 2), str(answer + 5)]
        explanation = f'{" + ".join(str(v) for v in values)} = {answer}'
        return {
            'skill_id': 'g3_data',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': explanation,
            'template_id': 'g3_data_total',
            'difficulty': estimate_difficulty(3, 0.5),
        }
    else:  # difference
        i, j = random.sample(range(4), 2)
        answer = abs(values[i] - values[j])
        question = f'A class survey shows: {table_desc}. How many more {items[i]} than {items[j]}?'
        if values[i] < values[j]:
            question = f'A class survey shows: {table_desc}. How many more {items[j]} than {items[i]}?'
        distractors = [str(answer + 1), str(answer + 2), str(values[i] + values[j])]
        explanation = f'{max(values[i], values[j])} - {min(values[i], values[j])} = {answer}'
        return {
            'skill_id': 'g3_data',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': explanation,
            'template_id': 'g3_data_difference',
            'difficulty': estimate_difficulty(3, 0.6),
        }


GRADE3_TEMPLATES = {
    'g3_mult_facts': [multiplication_facts],
    'g3_div_facts': [division_facts],
    'g3_multi_digit_mult': [multi_digit_multiply],
    'g3_area_perimeter': [area_perimeter],
    'g3_fraction_compare': [fraction_compare],
    'g3_fraction_add_sub': [fraction_add_sub],
    'g3_rounding': [rounding],
    'g3_mult_div_word': [mult_div_word_problems],
    'g3_elapsed_time': [elapsed_time],
    'g3_data': [data_interpretation],
}
