"""Local question generators that don't need an LLM — ported from kidtutor.

Currently supports: analog clock reading questions with SVG visuals.
"""
import math
import random

# Keywords that trigger clock question generation
CLOCK_KEYWORDS = {'clock', 'telling time', 'tell time', 'analog time',
                  'read time', 'reading time', 'reading clocks', 'analog clock'}


def is_clock_node(node_name, node_description=''):
    """Check if a curriculum node is about clock reading."""
    text = (node_name + ' ' + (node_description or '')).lower()
    return any(kw in text for kw in CLOCK_KEYWORDS)


def generate_clock_question(node_name, node_description='', recent_questions=None):
    """Generate a clock-reading question with an SVG clock face.

    Detects hour-only vs quarter-hour from node name/description.
    Returns (question_dict, 'local-clock', description_string).
    """
    recent_set = set(recent_questions or [])
    text_lower = (node_name + ' ' + (node_description or '')).lower()

    is_hour_only = ('hour' in text_lower and 'half' not in text_lower
                    and 'quarter' not in text_lower)

    if is_hour_only:
        candidates = [(h, 0) for h in range(1, 13)]
    else:
        candidates = [(h, m) for h in range(1, 13) for m in (0, 15, 30, 45)]

    random.shuffle(candidates)

    question_template = "What time does this clock show?"
    hour, minute = candidates[0]
    for h, m in candidates:
        answer = _format_clock_time(h, m)
        q_key = f"{question_template} [{answer}]"
        if q_key not in recent_set:
            hour, minute = h, m
            break

    correct = _format_clock_time(hour, minute)
    clock_svg = _generate_clock_svg(hour, minute)

    # Generate plausible wrong choices
    if is_hour_only:
        all_hours = list(range(1, 13))
        all_hours.remove(hour)
        distractors = random.sample(all_hours, 3)
        choices = [_format_clock_time(d, 0) for d in distractors] + [correct]
    else:
        wrong = set()
        possible_minutes = [0, 15, 30, 45]
        while len(wrong) < 3:
            wh = random.randint(1, 12)
            wm = random.choice(possible_minutes)
            t = _format_clock_time(wh, wm)
            if t != correct:
                wrong.add(t)
        choices = list(wrong) + [correct]

    random.shuffle(choices)

    if minute == 0:
        hint = ("Look where the short hand points — that's the hour. "
                "The long hand on 12 means o'clock.")
    elif minute == 30:
        hint = ("The long hand on 6 means half past. "
                "The short hand shows the hour.")
    elif minute == 15:
        hint = ("The long hand on 3 means quarter past. "
                "The short hand shows the hour.")
    else:
        hint = "The long hand on 9 means quarter to the next hour."

    q_data = {
        'question': f"{question_template} [{correct}]",
        'correct_answer': correct,
        'options': choices,
        'explanation': hint,
        'clock_svg': clock_svg,
    }

    return q_data, 'local-clock', f'Clock node: {node_name}'


def _format_clock_time(hour, minute):
    """Format time as H:MM string."""
    return f"{hour}:{minute:02d}"


def _generate_clock_svg(hour, minute, size=200):
    """Generate an analog clock face SVG showing the given time.

    Returns an SVG string with circle, hour numbers, hour/minute hands,
    center dot.
    """
    cx, cy = size / 2, size / 2
    r = size / 2 - 10

    parts = [
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" '
        f'stroke="#2C3E50" stroke-width="3"/>',
    ]

    # Hour tick marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = cx + (r - 8) * math.cos(angle)
        y1 = cy + (r - 8) * math.sin(angle)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="#2C3E50" stroke-width="2"/>'
        )

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
