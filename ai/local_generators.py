"""Local question generators that don't need an LLM — ported from kidtutor.

Supports: analog clock reading, inequality number line diagrams.
"""
import math
import random

# Keywords that trigger clock question generation
CLOCK_KEYWORDS = {'clock', 'telling time', 'tell time', 'analog time',
                  'read time', 'reading time', 'reading clocks', 'analog clock'}

# Keywords that trigger inequality number line generation
INEQUALITY_KEYWORDS = {'inequality', 'inequalities', 'number line',
                       'number lines', 'graphing inequalities'}


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


# ---------------------------------------------------------------------------
# Inequality number line generator
# ---------------------------------------------------------------------------

def is_inequality_node(node_name, node_description=''):
    """Check if a curriculum node is about inequalities / number lines."""
    text = (node_name + ' ' + (node_description or '')).lower()
    return any(kw in text for kw in INEQUALITY_KEYWORDS)


_OPERATORS = ['>', '<', '>=', '<=']
_OP_LABELS = {'>': '>', '<': '<', '>=': '\u2265', '<=': '\u2264'}


def generate_inequality_question(node_name, node_description='',
                                 recent_questions=None):
    """Generate an inequality question with a number line SVG diagram.

    Returns (question_dict, 'local-inequality', description_string).
    """
    recent_set = set(recent_questions or [])

    # Try to find a combination not recently used
    candidates = [(op, val) for op in _OPERATORS for val in range(-5, 6)]
    random.shuffle(candidates)

    op, boundary = candidates[0]
    for o, v in candidates:
        q_key = f"Which inequality does this number line represent? [x {o} {v}]"
        if q_key not in recent_set:
            op, boundary = o, v
            break

    # Build correct answer and distractors
    correct = f"x {_OP_LABELS[op]} {boundary}"
    # Distractors: same boundary, different operators
    other_ops = [o for o in _OPERATORS if o != op]
    distractors = [f"x {_OP_LABELS[o]} {boundary}" for o in other_ops]
    choices = distractors[:3] + [correct]
    random.shuffle(choices)

    # Generate SVG
    svg = _generate_number_line_svg(op, boundary)

    # Explanation
    circle_type = 'filled' if op in ('>=', '<=') else 'open'
    direction = 'right' if op in ('>', '>=') else 'left'
    explanation = (
        f"The {circle_type} circle at {boundary} means the value {boundary} "
        f"{'is' if circle_type == 'filled' else 'is not'} included. "
        f"The shading goes to the {direction}, representing all values "
        f"{'greater than' if direction == 'right' else 'less than'}"
        f"{' or equal to' if op in ('>=', '<=') else ''} {boundary}."
    )

    q_data = {
        'question': f"Which inequality does this number line represent? "
                    f"[x {op} {boundary}]",
        'correct_answer': correct,
        'options': choices,
        'explanation': explanation,
        'number_line_svg': svg,
    }

    return q_data, 'local-inequality', f'Inequality node: {node_name}'


def _generate_number_line_svg(operator, boundary, width=420, height=80):
    """Generate a number line SVG for an inequality.

    Shows a horizontal line with tick marks, an open/filled circle at the
    boundary, and a colored region + arrow for the solution set.
    """
    # Layout
    margin = 30
    line_y = 35
    label_y = 60
    usable = width - 2 * margin

    # Range: show boundary +/- 4, at least -5 to 5
    low = min(boundary - 4, -5)
    high = max(boundary + 4, 5)
    n_ticks = high - low + 1
    spacing = usable / (n_ticks - 1)

    def x_for(val):
        return margin + (val - low) * spacing

    bx = x_for(boundary)
    is_inclusive = operator in ('>=', '<=')
    goes_right = operator in ('>', '>=')
    color = '#3498DB'

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">',
    ]

    # Main line with arrow tips
    parts.append(
        f'<line x1="{margin - 15}" y1="{line_y}" x2="{width - margin + 15}" '
        f'y2="{line_y}" stroke="#2C3E50" stroke-width="1.5"/>'
    )
    # Left arrow
    parts.append(
        f'<polygon points="{margin - 15},{line_y} {margin - 7},{line_y - 5} '
        f'{margin - 7},{line_y + 5}" fill="#2C3E50"/>'
    )
    # Right arrow
    parts.append(
        f'<polygon points="{width - margin + 15},{line_y} '
        f'{width - margin + 7},{line_y - 5} '
        f'{width - margin + 7},{line_y + 5}" fill="#2C3E50"/>'
    )

    # Tick marks and labels
    for val in range(low, high + 1):
        x = x_for(val)
        tick_h = 8 if val == 0 else 5
        parts.append(
            f'<line x1="{x:.1f}" y1="{line_y - tick_h}" '
            f'x2="{x:.1f}" y2="{line_y + tick_h}" '
            f'stroke="#2C3E50" stroke-width="1.5"/>'
        )
        font_weight = 'bold' if val == 0 else 'normal'
        parts.append(
            f'<text x="{x:.1f}" y="{label_y}" text-anchor="middle" '
            f'font-size="12" font-family="sans-serif" fill="#2C3E50" '
            f'font-weight="{font_weight}">{val}</text>'
        )

    # Solution region (thick colored line with arrow)
    if goes_right:
        parts.append(
            f'<line x1="{bx:.1f}" y1="{line_y}" '
            f'x2="{width - margin + 12:.1f}" y2="{line_y}" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
        # Arrow head
        ax = width - margin + 12
        parts.append(
            f'<polygon points="{ax},{line_y} {ax - 8},{line_y - 5} '
            f'{ax - 8},{line_y + 5}" fill="{color}"/>'
        )
    else:
        parts.append(
            f'<line x1="{margin - 12:.1f}" y1="{line_y}" '
            f'x2="{bx:.1f}" y2="{line_y}" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
        # Arrow head
        ax = margin - 12
        parts.append(
            f'<polygon points="{ax},{line_y} {ax + 8},{line_y - 5} '
            f'{ax + 8},{line_y + 5}" fill="{color}"/>'
        )

    # Boundary circle (open or filled)
    if is_inclusive:
        parts.append(
            f'<circle cx="{bx:.1f}" cy="{line_y}" r="6" '
            f'fill="{color}" stroke="{color}" stroke-width="2"/>'
        )
    else:
        parts.append(
            f'<circle cx="{bx:.1f}" cy="{line_y}" r="6" '
            f'fill="white" stroke="{color}" stroke-width="2.5"/>'
        )

    parts.append('</svg>')
    return '\n'.join(parts)
