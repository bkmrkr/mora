"""Common utilities for question templates — distractor generation, shuffling."""
import math
import random

# ELO difficulty bands per grade (each spans ~250 ELO points)
GRADE_DIFFICULTY = {1: (500, 750), 2: (700, 950), 3: (900, 1150), 4: (1100, 1350)}


def estimate_difficulty(grade, complexity):
    """Estimate intrinsic ELO difficulty from grade and complexity (0.0–1.0).

    complexity=0.0 → easiest question for that grade
    complexity=1.0 → hardest question for that grade
    """
    low, high = GRADE_DIFFICULTY.get(grade, (800, 1000))
    return round(low + complexity * (high - low))


def generate_clock_svg(hour, minute, size=200):
    """Generate an analog clock face SVG showing the given time.

    Returns an SVG string with circle, hour numbers, hour/minute hands, center dot.
    """
    cx, cy = size / 2, size / 2
    r = size / 2 - 10

    parts = [
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" stroke="#2C3E50" stroke-width="3"/>',
    ]

    # Hour tick marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = cx + (r - 8) * math.cos(angle)
        y1 = cy + (r - 8) * math.sin(angle)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#2C3E50" stroke-width="2"/>')

    # Hour numbers
    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        nx = cx + (r - 22) * math.cos(angle)
        ny = cy + (r - 22) * math.sin(angle)
        parts.append(
            f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="{size // 10}" '
            f'font-family="sans-serif" fill="#2C3E50">{i}</text>'
        )

    # Minute hand (long, thin)
    min_angle = math.radians(minute * 6 - 90)
    min_len = r - 30
    mx = cx + min_len * math.cos(min_angle)
    my = cy + min_len * math.sin(min_angle)
    parts.append(
        f'<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" '
        f'stroke="#2C3E50" stroke-width="2.5" stroke-linecap="round"/>'
    )

    # Hour hand (short, thick) — accounts for fractional hour from minutes
    hour_fraction = hour + minute / 60.0
    hr_angle = math.radians(hour_fraction * 30 - 90)
    hr_len = r * 0.55
    hx = cx + hr_len * math.cos(hr_angle)
    hy = cy + hr_len * math.sin(hr_angle)
    parts.append(
        f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" '
        f'stroke="#2C3E50" stroke-width="4" stroke-linecap="round"/>'
    )

    # Center dot
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#2C3E50"/>')
    parts.append('</svg>')
    return '\n'.join(parts)


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
    elif '/' in correct_str:
        # Fraction answer — generate fraction distractors
        try:
            num, den = correct_str.split('/')
            num, den = int(num), int(den)
            for n_off, d_off in [(1, 0), (-1, 0), (0, 1), (1, 1), (-1, 1), (2, 0)]:
                if len(opts) >= 3:
                    break
                cn = num + n_off
                cd = den + d_off
                if cn > 0 and cd > 0:
                    candidate = f'{cn}/{cd}'
                    if candidate not in seen:
                        opts.append(candidate)
                        seen.add(candidate)
        except (ValueError, TypeError):
            pass
    else:
        # Try float padding (for decimal answers)
        try:
            correct_float = float(correct_str)
            for offset in [0.1, -0.1, 0.2, -0.2, 1.0, -1.0, 0.5]:
                if len(opts) >= 3:
                    break
                val = round(correct_float + offset, 2)
                if val >= 0:
                    candidate = str(val)
                    if candidate not in seen:
                        opts.append(candidate)
                        seen.add(candidate)
        except (ValueError, TypeError):
            pass

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
