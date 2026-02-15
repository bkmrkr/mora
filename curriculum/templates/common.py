"""Common utilities for question templates — distractor generation, shuffling."""
import random


def arithmetic_distractors(answer, a, b, op='+', count=3):
    """Generate plausible wrong answers for arithmetic questions.

    Uses common-error patterns: off-by-one, wrong operation, digit errors.
    """
    distractors = set()
    ans = int(answer) if isinstance(answer, str) else answer

    # Off-by-one
    distractors.add(ans + 1)
    distractors.add(ans - 1)

    # Off-by-two
    distractors.add(ans + 2)
    distractors.add(ans - 2)

    # Wrong operation errors
    if op == '+':
        distractors.add(abs(a - b))  # subtracted instead
    elif op == '-':
        distractors.add(a + b)  # added instead
    elif op == '*':
        distractors.add(a + b)  # added instead of multiplied
    elif op == '/':
        if b != 0:
            distractors.add(a * b)  # multiplied instead

    # Remove the correct answer and negatives
    distractors.discard(ans)
    distractors = {d for d in distractors if d >= 0}

    result = list(distractors)
    random.shuffle(result)
    return [str(d) for d in result[:count]]


def make_options(correct, distractors):
    """Combine correct answer with distractors and shuffle. Always 4 unique options."""
    correct_str = str(correct)

    # Deduplicate distractors, excluding the correct answer
    seen = {correct_str}
    opts = []
    for d in distractors:
        d_str = str(d)
        if d_str not in seen:
            opts.append(d_str)
            seen.add(d_str)
        if len(opts) == 3:
            break

    # Pad if we don't have enough unique distractors
    correct_int = None
    try:
        correct_int = int(correct_str)
    except (ValueError, TypeError):
        pass

    if correct_int is not None:
        for offset in [-3, 3, -4, 4, 5, -5, 6, -6, 7]:
            if len(opts) >= 3:
                break
            candidate = str(correct_int + offset)
            if candidate not in seen and int(candidate) >= 0:
                opts.append(candidate)
                seen.add(candidate)

    all_opts = opts[:3] + [correct_str]
    random.shuffle(all_opts)
    return all_opts


def word_problem_frame(a, b, op, answer):
    """Generate a simple word problem for add/sub."""
    add_templates = [
        f"Emma has {a} apples. She gets {b} more. How many apples does she have now?",
        f"There are {a} birds in a tree. {b} more birds land. How many birds are there?",
        f"Sam has {a} stickers. His friend gives him {b} more. How many stickers does Sam have?",
        f"A jar has {a} marbles. You put in {b} more. How many marbles are in the jar?",
        f"There are {a} books on a shelf. You add {b} more. How many books are on the shelf?",
    ]
    sub_templates = [
        f"Emma has {a} apples. She gives away {b}. How many apples does she have left?",
        f"There are {a} birds in a tree. {b} fly away. How many birds are left?",
        f"Sam has {a} stickers. He gives {b} to a friend. How many stickers does Sam have?",
        f"A jar has {a} marbles. You take out {b}. How many marbles are in the jar?",
        f"There are {a} cookies. You eat {b}. How many cookies are left?",
    ]

    if op == '+':
        return random.choice(add_templates)
    else:
        return random.choice(sub_templates)
