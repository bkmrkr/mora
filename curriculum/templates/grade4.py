"""Grade 4 math question templates — 10 skills.

Each function takes difficulty_elo and returns a dict:
  question, correct_answer, options, explanation, template_id, skill_id
"""
import random
from math import gcd, lcm

from curriculum.templates.common import arithmetic_distractors, make_options, estimate_difficulty


def multi_digit_multiply(difficulty_elo):
    """g4_multi_digit_mult: 2-digit × 2-digit multiplication."""
    if difficulty_elo < 750:
        a = random.randint(10, 30)
        b = random.randint(10, 20)
    else:
        a = random.randint(10, 99)
        b = random.randint(10, 50)

    answer = a * b
    distractors = arithmetic_distractors(answer, a, b, op='*')
    return {
        'skill_id': 'g4_multi_digit_mult',
        'question': f'What is {a} × {b}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} × {b} = {answer}',
        'template_id': 'g4_multi_digit_mult',
        'difficulty': estimate_difficulty(4, min(answer / 4950, 1.0)),
    }


def long_division(difficulty_elo):
    """g4_long_division: Division with 2+ digit dividends."""
    if difficulty_elo < 750:
        divisor = random.randint(2, 9)
        quotient = random.randint(10, 30)
    else:
        divisor = random.randint(2, 12)
        quotient = random.randint(10, 80)

    dividend = divisor * quotient
    answer = quotient
    distractors = arithmetic_distractors(answer, dividend, divisor, op='/')
    return {
        'skill_id': 'g4_long_division',
        'question': f'What is {dividend} ÷ {divisor}?',
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{dividend} ÷ {divisor} = {answer}',
        'template_id': 'g4_long_division',
        'difficulty': estimate_difficulty(4, min(dividend / 960, 1.0)),
    }


def fraction_ops(difficulty_elo):
    """g4_fraction_ops: Add/sub fractions with unlike denominators."""
    dens = [(2, 4), (3, 6), (2, 3), (3, 4), (4, 8), (2, 6), (5, 10), (4, 6)]
    d1, d2 = random.choice(dens)
    op = random.choice(['+', '-'])

    lcd = lcm(d1, d2)

    # Pick numerators; for subtraction, ensure non-zero result
    n1 = random.randint(1, d1 - 1)
    n2 = random.randint(1, d2 - 1)
    adj_n1 = n1 * (lcd // d1)
    adj_n2 = n2 * (lcd // d2)

    if op == '-' and adj_n1 == adj_n2:
        # Equivalent fractions — regenerate to avoid zero result
        while adj_n1 == adj_n2:
            n1 = random.randint(1, d1 - 1)
            n2 = random.randint(1, d2 - 1)
            adj_n1 = n1 * (lcd // d1)
            adj_n2 = n2 * (lcd // d2)

    if op == '+':
        result_num = adj_n1 + adj_n2
    else:
        if adj_n1 < adj_n2:
            n1, n2 = n2, n1
            d1, d2 = d2, d1
            adj_n1, adj_n2 = adj_n2, adj_n1
        result_num = adj_n1 - adj_n2

    # Simplify
    g = gcd(result_num, lcd)
    final_num = result_num // g
    final_den = lcd // g
    answer = f'{final_num}/{final_den}'

    # Common mistakes
    wrong1 = f'{n1 + n2}/{d1 + d2}' if op == '+' else f'{abs(n1 - n2)}/{abs(d1 - d2) or 1}'
    wrong2 = f'{result_num}/{lcd}'  # unsimplified (if different from answer)
    wrong3 = f'{final_num + 1}/{final_den}'

    distractors = [d for d in [wrong1, wrong2, wrong3] if d != answer]

    return {
        'skill_id': 'g4_fraction_ops',
        'question': f'What is {n1}/{d1} {op} {n2}/{d2}?',
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'{n1}/{d1} {op} {n2}/{d2} = {adj_n1}/{lcd} {op} {adj_n2}/{lcd} = {answer}',
        'template_id': f'g4_fraction_ops_{op}',
        'difficulty': estimate_difficulty(4, 0.4 + lcd / 24),
    }


def decimal_place_value(difficulty_elo):
    """g4_decimal_place_value: Understand decimal place values."""
    if difficulty_elo < 750:
        # Tenths
        whole = random.randint(0, 9)
        tenth = random.randint(1, 9)
        number = f'{whole}.{tenth}'
        place = 'tenths'
        answer = str(tenth)
        question = f'What digit is in the tenths place of {number}?'
        distractors = [str(whole), str((tenth + 1) % 10), str(random.randint(0, 9))]
    else:
        # Hundredths
        whole = random.randint(0, 9)
        tenth = random.randint(0, 9)
        hundredth = random.randint(1, 9)
        number = f'{whole}.{tenth}{hundredth}'
        variant = random.choice(['tenths', 'hundredths'])
        if variant == 'tenths':
            answer = str(tenth)
            place = 'tenths'
        else:
            answer = str(hundredth)
            place = 'hundredths'
        question = f'What digit is in the {place} place of {number}?'
        distractors = [str(whole), str(tenth if place == 'hundredths' else hundredth),
                       str(random.randint(0, 9))]

    distractors = [d for d in distractors if d != answer]
    return {
        'skill_id': 'g4_decimal_place_value',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'The {place} digit of {number} is {answer}.',
        'template_id': f'g4_decimal_place_value_{place}',
        'difficulty': estimate_difficulty(4, 0.2 if place == 'tenths' else 0.5),
    }


def decimal_add_sub(difficulty_elo):
    """g4_decimal_add_sub: Add and subtract decimals."""
    op = random.choice(['+', '-'])
    if difficulty_elo < 750:
        a = round(random.randint(10, 99) / 10, 1)
        b = round(random.randint(10, 50) / 10, 1)
    else:
        a = round(random.randint(100, 999) / 100, 2)
        b = round(random.randint(100, 500) / 100, 2)

    if op == '-' and a < b:
        a, b = b, a

    answer = round(a + b, 2) if op == '+' else round(a - b, 2)
    question = f'What is {a} {op} {b}?'
    distractors = [str(round(answer + 0.1, 2)), str(round(answer - 0.1, 2)),
                   str(round(answer + 1, 2))]
    distractors = [d for d in distractors if float(d) >= 0 and d != str(answer)]

    return {
        'skill_id': 'g4_decimal_add_sub',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': f'{a} {op} {b} = {answer}',
        'template_id': f'g4_decimal_add_sub_{op}',
        'difficulty': estimate_difficulty(4, 0.3 + min(max(a, b) / 10, 0.7)),
    }


def angles(difficulty_elo):
    """g4_angles: Classify and measure angles."""
    if difficulty_elo < 750:
        variant = random.choice(['classify', 'identify', 'range'])
        if variant == 'classify':
            # Classify angle type from measurement
            angle = random.choice([
                (random.randint(10, 80), 'acute'),
                (90, 'right'),
                (random.randint(100, 170), 'obtuse'),
            ])
            degrees, correct = angle
            question = f'An angle measures {degrees}°. What type of angle is it?'
            wrong = [t for t in ['acute', 'right', 'obtuse', 'straight'] if t != correct]
            explanation = f'A {degrees}° angle is {correct} ({"less than 90°" if correct == "acute" else "exactly 90°" if correct == "right" else "greater than 90°"}).'
        elif variant == 'identify':
            # Pick an angle type and ask for an example
            atype = random.choice(['acute', 'right', 'obtuse'])
            if atype == 'acute':
                correct = str(random.choice([15, 25, 30, 45, 60, 75]))
                wrong_vals = ['90', '120', '180']
            elif atype == 'right':
                correct = '90'
                wrong_vals = ['45', '120', '180']
            else:
                correct = str(random.choice([100, 110, 120, 135, 150, 170]))
                wrong_vals = ['45', '90', '180']
            article = 'an' if atype in ('acute', 'obtuse') else 'a'
            question = f'Which of these is {article} {atype} angle?'
            wrong = wrong_vals
            explanation = f'{correct}° is {atype} ({"less than 90°" if atype == "acute" else "exactly 90°" if atype == "right" else "between 90° and 180°"}).'
        else:
            # What range does a type fall in?
            atype = random.choice(['acute', 'right', 'obtuse', 'straight'])
            ranges = {
                'acute': ('less than 90°', ['exactly 90°', 'between 90° and 180°', 'exactly 180°']),
                'right': ('exactly 90°', ['less than 90°', 'between 90° and 180°', 'exactly 180°']),
                'obtuse': ('between 90° and 180°', ['less than 90°', 'exactly 90°', 'exactly 180°']),
                'straight': ('exactly 180°', ['less than 90°', 'exactly 90°', 'between 90° and 180°']),
            }
            correct, wrong = ranges[atype]
            article = 'An' if atype in ('acute', 'obtuse') else 'A'
            question = f'{article} {atype} angle measures...'
            explanation = f'{article} {atype} angle measures {correct}.'

        return {
            'skill_id': 'g4_angles',
            'question': question,
            'correct_answer': correct,
            'options': make_options(correct, wrong[:3]),
            'explanation': explanation,
            'template_id': 'g4_angles_classify',
            'difficulty': estimate_difficulty(4, 0.2),
        }
    else:
        # Complementary / supplementary
        variant = random.choice(['complementary', 'supplementary'])
        if variant == 'complementary':
            a = random.randint(10, 80)
            answer = 90 - a
            question = f'Two angles are complementary. One angle is {a}°. What is the other angle?'
            explanation = f'Complementary angles add to 90°. {a}° + {answer}° = 90°.'
        else:
            a = random.randint(10, 170)
            answer = 180 - a
            question = f'Two angles are supplementary. One angle is {a}°. What is the other angle?'
            explanation = f'Supplementary angles add to 180°. {a}° + {answer}° = 180°.'

        distractors = [str(answer + 10), str(answer - 10), str(a)]
        distractors = [d for d in distractors if int(d) > 0 and d != str(answer)]
        return {
            'skill_id': 'g4_angles',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': explanation,
            'template_id': f'g4_angles_{variant}',
            'difficulty': estimate_difficulty(4, 0.5 if variant == 'complementary' else 0.7),
        }


def geometry_lines(difficulty_elo):
    """g4_geometry: Identify parallel and perpendicular lines."""
    if difficulty_elo < 750:
        variants = [
            {
                'question': 'Parallel lines are lines that...',
                'answer': 'never cross',
                'distractors': ['cross at a right angle', 'cross at any angle', 'are the same line'],
                'explanation': 'Parallel lines go in the same direction and never cross.',
                'tid': 'parallel_def',
            },
            {
                'question': 'Perpendicular lines are lines that...',
                'answer': 'cross at a right angle',
                'distractors': ['never cross', 'are curved', 'go in the same direction'],
                'explanation': 'Perpendicular lines meet at a 90-degree (right) angle.',
                'tid': 'perpendicular_def',
            },
            {
                'question': 'What kind of lines never cross each other?',
                'answer': 'parallel',
                'distractors': ['perpendicular', 'diagonal', 'curved'],
                'explanation': 'Parallel lines go in the same direction and never cross.',
                'tid': 'parallel_id',
            },
            {
                'question': 'What kind of lines meet at a right angle (90°)?',
                'answer': 'perpendicular',
                'distractors': ['parallel', 'diagonal', 'horizontal'],
                'explanation': 'Perpendicular lines cross at exactly 90 degrees.',
                'tid': 'perpendicular_id',
            },
            {
                'question': 'Railroad tracks are an example of _____ lines.',
                'answer': 'parallel',
                'distractors': ['perpendicular', 'curved', 'intersecting'],
                'explanation': 'Railroad tracks run side by side and never cross — they are parallel.',
                'tid': 'parallel_real',
            },
            {
                'question': 'The corner of a book shows _____ lines.',
                'answer': 'perpendicular',
                'distractors': ['parallel', 'curved', 'diagonal'],
                'explanation': 'The edges of a book corner meet at a right angle — they are perpendicular.',
                'tid': 'perpendicular_real',
            },
            {
                'question': 'What angle do perpendicular lines make?',
                'answer': '90 degrees',
                'distractors': ['45 degrees', '180 degrees', '60 degrees'],
                'explanation': 'Perpendicular lines always cross at 90 degrees (a right angle).',
                'tid': 'perpendicular_angle',
            },
        ]
        v = random.choice(variants)
        question = v['question']
        answer = v['answer']
        distractors = v['distractors']
        explanation = v['explanation']
        template_id = f'g4_geometry_{v["tid"]}'
    else:
        shapes_data = [
            ('square', 2, 4),  # (parallel pairs, right angles)
            ('rectangle', 2, 4),
            ('triangle', 0, 0),
            ('trapezoid', 1, 0),
        ]
        shape, par, perp = random.choice(shapes_data)
        prop = random.choice(['parallel', 'perpendicular'])
        if prop == 'parallel':
            answer = str(par)
            question = f'How many pairs of parallel sides does a {shape} have?'
            explanation = f'A {shape} has {par} pair{"s" if par != 1 else ""} of parallel sides.'
        else:
            answer = str(perp)
            question = f'How many right angles does a {shape} have?'
            explanation = f'A {shape} has {perp} right angle{"s" if perp != 1 else ""}.'

        distractors = [str(int(answer) + 1), str(int(answer) + 2),
                       str(max(0, int(answer) - 1))]
        distractors = [d for d in distractors if d != answer]
        return {
            'skill_id': 'g4_geometry',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, distractors),
            'explanation': explanation,
            'template_id': f'g4_geometry_{prop}',
            'difficulty': estimate_difficulty(4, 0.5),
        }

    return {
        'skill_id': 'g4_geometry',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': explanation,
        'template_id': template_id,
        'difficulty': estimate_difficulty(4, 0.3),
    }


def factors_multiples(difficulty_elo):
    """g4_factors_multiples: Find factors and multiples."""
    if difficulty_elo < 750:
        # List factors
        n = random.choice([12, 16, 18, 20, 24, 30, 36])
        all_factors = [i for i in range(1, n + 1) if n % i == 0]
        target_factor = random.choice(all_factors[1:-1])  # not 1 or n
        question = f'Is {target_factor} a factor of {n}?'
        answer = 'yes'
        return {
            'skill_id': 'g4_factors_multiples',
            'question': question,
            'correct_answer': answer,
            'options': make_options(answer, ['no', 'only sometimes', 'cannot tell']),
            'explanation': f'{n} ÷ {target_factor} = {n // target_factor}, so yes, {target_factor} is a factor of {n}.',
            'template_id': 'g4_factors_is_factor',
            'difficulty': estimate_difficulty(4, 0.3),
        }
    else:
        # Find multiples
        n = random.randint(3, 12)
        pos = random.randint(3, 8)
        answer = n * pos
        suffix = 'rd' if pos == 3 else 'th'
        question = f'What is the {pos}{suffix} multiple of {n}?'
        distractors = [str(n * (pos + 1)), str(n * (pos - 1)), str(n + pos)]
        return {
            'skill_id': 'g4_factors_multiples',
            'question': question,
            'correct_answer': str(answer),
            'options': make_options(str(answer), distractors),
            'explanation': f'{n} × {pos} = {answer}',
            'template_id': 'g4_factors_multiples',
            'difficulty': estimate_difficulty(4, 0.4 + n / 24),
        }


def multi_step_word(difficulty_elo):
    """g4_multi_step_word: Multi-step word problems."""
    variant = random.choice(['mult_add', 'mult_sub', 'divide_add'])

    if variant == 'mult_add':
        packs = random.randint(2, 6)
        per_pack = random.randint(4, 10)
        extra = random.randint(1, 8)
        answer = packs * per_pack + extra
        loose_word = 'loose one' if extra == 1 else 'loose ones'
        question = (f'A store has {packs} packs of juice boxes with {per_pack} in each pack, '
                    f'plus {extra} {loose_word}. How many juice boxes in total?')
        explanation = f'{packs} × {per_pack} = {packs * per_pack}, then {packs * per_pack} + {extra} = {answer}'
    elif variant == 'mult_sub':
        groups = random.randint(3, 8)
        per_group = random.randint(3, 8)
        used = random.randint(1, groups * per_group // 2)
        answer = groups * per_group - used
        eaten_phrase = '1 apple is eaten' if used == 1 else f'{used} apples are eaten'
        question = (f'There are {groups} baskets with {per_group} apples each. '
                    f'If {eaten_phrase}, how many are left?')
        explanation = f'{groups} × {per_group} = {groups * per_group}, then {groups * per_group} - {used} = {answer}'
    else:
        groups = random.choice([2, 3, 4, 5, 6])
        per_group_base = random.randint(4, 12)
        total = groups * per_group_base
        extra = random.randint(2, 8)
        per_group = total // groups
        answer = per_group + extra
        question = (f'A teacher has {total} pencils to share equally among {groups} groups, '
                    f'plus {extra} extra pencils for each group. How many pencils does each group get?')
        explanation = f'{total} ÷ {groups} = {per_group}, then {per_group} + {extra} = {answer}'

    distractors = arithmetic_distractors(answer, answer, 0)
    return {
        'skill_id': 'g4_multi_step_word',
        'question': question,
        'correct_answer': str(answer),
        'options': make_options(str(answer), distractors),
        'explanation': explanation,
        'template_id': f'g4_multi_step_word_{variant}',
        'difficulty': estimate_difficulty(4, 0.5 + answer / 100),
    }


def equivalent_fractions(difficulty_elo):
    """g4_equivalent_fractions: Find equivalent fractions."""
    if difficulty_elo < 750:
        # Simple: multiply to find equivalent
        num = random.randint(1, 4)
        den = random.randint(num + 1, 8)
        multiplier = random.randint(2, 4)
        eq_num = num * multiplier
        eq_den = den * multiplier

        variant = random.choice(['find_num', 'find_den'])
        if variant == 'find_num':
            question = f'{num}/{den} = ?/{eq_den}'
            answer = str(eq_num)
            distractors = [str(eq_num + 1), str(eq_num - 1), str(num + den)]
        else:
            question = f'{num}/{den} = {eq_num}/?'
            answer = str(eq_den)
            distractors = [str(eq_den + 1), str(eq_den - 1), str(eq_num + eq_den)]
    else:
        # Which fraction is equivalent
        num = random.randint(1, 5)
        den = random.randint(num + 1, 10)
        mult = random.randint(2, 4)
        eq = f'{num * mult}/{den * mult}'
        wrong1 = f'{num + 1}/{den + 1}'
        wrong2 = f'{num * mult}/{den * mult + 1}'
        wrong3 = f'{num}/{den + mult}'
        question = f'Which fraction is equivalent to {num}/{den}?'
        answer = eq
        distractors = [wrong1, wrong2, wrong3]

    return {
        'skill_id': 'g4_equivalent_fractions',
        'question': question,
        'correct_answer': answer,
        'options': make_options(answer, distractors),
        'explanation': f'{num}/{den} × {multiplier}/{multiplier} = {eq_num}/{eq_den}' if difficulty_elo < 750 else f'{num}/{den} = {eq}',
        'template_id': 'g4_equivalent_fractions',
        'difficulty': estimate_difficulty(4, 0.3 if difficulty_elo < 750 else 0.7),
    }


GRADE4_TEMPLATES = {
    'g4_multi_digit_mult': [multi_digit_multiply],
    'g4_long_division': [long_division],
    'g4_fraction_ops': [fraction_ops],
    'g4_decimal_place_value': [decimal_place_value],
    'g4_decimal_add_sub': [decimal_add_sub],
    'g4_angles': [angles],
    'g4_geometry': [geometry_lines],
    'g4_factors_multiples': [factors_multiples],
    'g4_multi_step_word': [multi_step_word],
    'g4_equivalent_fractions': [equivalent_fractions],
}
