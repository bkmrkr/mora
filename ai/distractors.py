"""Compute distractors algorithmically for MCQ questions.

This ensures distractors are always valid (not wrong answers from LLM).
"""
import random
import re


def compute_distractors(correct_answer, num_options=4):
    """Compute plausible distractors for a numeric or simple text answer.

    Strategies:
    - For numbers: correct±1, correct×2, correct÷2, random nearby
    - For fractions: nearby fractions
    - For simple text: variants with common mistakes

    Returns list of distractor strings (without letter prefixes).
    """
    import re
    LETTER_PREFIX_RE = re.compile(r'^[A-Da-d][).\s]+\s*')

    # Strip any existing letter prefix first
    correct_str = LETTER_PREFIX_RE.sub('', str(correct_answer)).strip()

    # Try numeric strategies first
    num = _parse_number(correct_str)
    if num is not None:
        distractors = _numeric_distractors(num)
    else:
        # Fall back to text-based distractors
        distractors = _text_distractors(correct_str)

    # Ensure we have enough distractors (avoid duplicates)
    attempts = 0
    while len(distractors) < num_options - 1 and attempts < 10:
        new_distractor = _fallback_distractor(correct_str, exclude=set(distractors) | {correct_str})
        if new_distractor not in distractors and new_distractor != correct_str:
            distractors.append(new_distractor)
        attempts += 1

    # Shuffle and return (num_options - 1) distractors
    random.shuffle(distractors)
    return distractors[:num_options - 1]


def _parse_number(text):
    """Parse a string as a number (int or float)."""
    text = text.strip()

    # Handle fractions like "1/2"
    if '/' in text:
        try:
            num, den = text.split('/')
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None

    # Handle LaTeX fractions: \frac{1}{2}
    m = re.search(r'\\frac\{(\d+)\}\{(\d+)\}', text)
    if m:
        try:
            return float(m.group(1)) / float(m.group(2))
        except (ValueError, ZeroDivisionError):
            return None

    # Handle simple expressions: sqrt(16), 2^2
    if 'sqrt' in text.lower():
        m = re.search(r'sqrt\((\d+)\)', text, re.IGNORECASE)
        if m:
            return float(m.group(1)) ** 0.5

    if '^' in text:
        m = re.search(r'(\d+)\s*\^\s*(\d+)', text)
        if m:
            try:
                return float(m.group(1)) ** float(m.group(2))
            except (ValueError, OverflowError):
                return None

    # Try direct parse
    try:
        return float(text)
    except ValueError:
        return None


def _numeric_distractors(correct):
    """Generate numeric distractors based on the correct answer."""
    distractors = []
    is_integer = (correct == int(correct))
    is_negative = correct < 0

    # Strategy 1: correct ± 1 (or ±0.5 for small numbers)
    if abs(correct) < 10:
        step = 1 if is_integer else 0.5
    else:
        step = max(1, int(abs(correct) * 0.1))  # 10% for larger numbers

    for delta in [step, -step, step * 2, -step * 2]:
        val = correct + delta
        if val != correct and val >= 0:  # Avoid negative for age/count questions
            d = _format_number(val, is_integer)
            if d not in distractors:
                distractors.append(d)

    # Strategy 2: multiplication/division errors
    if correct != 0:
        for mult in [2, 0.5]:
            val = correct * mult
            if val != correct and val >= 0:
                d = _format_number(val, is_integer)
                if d not in distractors:
                    distractors.append(d)

    # Strategy 3: common computation errors (addition vs subtraction)
    if abs(correct) > 5:
        val = correct + random.choice([-1, 1]) * random.randint(1, 3)
        if val != correct and val >= 0:
            d = _format_number(val, is_integer)
            if d not in distractors:
                distractors.append(d)

    # Strategy 4: random nearby numbers
    for _ in range(3):
        val = correct + random.randint(-int(max(5, abs(correct))), int(max(5, abs(correct))))
        if val != correct and val >= 0:
            d = _format_number(val, is_integer)
            if d not in distractors:
                distractors.append(d)

    return distractors


def _format_number(num, is_integer):
    """Format a number appropriately."""
    if is_integer or num == int(num):
        return str(int(num))
    # Round to 2 decimal places for clean display
    return f"{num:.2f}".rstrip('0').rstrip('.')


def _multi_value_distractors(correct):
    """Generate distractors for multi-value answers like '2, 3'.

    Strategies:
    - Off-by-one for each value
    - Swapped order
    - Only first value
    - Only second value
    """
    distractors = []

    # Parse comma-separated values
    parts = [p.strip() for p in correct.split(',')]
    if len(parts) < 2:
        return distractors

    # Try to extract numeric values
    nums = []
    for part in parts:
        # Extract just the number part (e.g., "2" from "x=2")
        m = re.search(r'-?\d+\.?\d*', part)
        if m:
            nums.append(float(m.group()))
        else:
            return distractors  # Can't parse, give up

    if not nums or len(nums) != len(parts):
        return distractors

    # Strategy 1: Off-by-one for each value
    for offset in [1, -1]:
        variant_parts = []
        for i, part in enumerate(parts):
            new_num = nums[i] + offset
            # Reconstruct the part (e.g., "x=3" from "x=2" with offset 1)
            if '=' in part:
                var_name = part.split('=')[0].strip()
                variant_parts.append(f"{var_name} = {int(new_num) if new_num == int(new_num) else new_num}")
            else:
                variant_parts.append(str(int(new_num)) if new_num == int(new_num) else str(new_num))
        variant = ', '.join(variant_parts)
        if variant != correct:
            distractors.append(variant)

    # Strategy 2: Swapped order
    if len(nums) == 2:
        swapped_parts = [parts[1], parts[0]]
        swapped = ', '.join(swapped_parts)
        if swapped != correct:
            distractors.append(swapped)

    # Strategy 3: Only first value
    if len(nums) >= 2:
        first_only = parts[0]
        if first_only != correct:
            distractors.append(first_only)

    # Strategy 4: Only second value
    if len(nums) >= 2:
        second_only = parts[1]
        if second_only != correct:
            distractors.append(second_only)

    return distractors


def _text_distractors(correct):
    """Generate text-based distractors for non-numeric answers."""
    # Common wrong answers for common question types
    distractors = []

    # For true/false questions
    if correct.lower() in ('true', 'false'):
        return ['True', 'False'] if correct.lower() == 'false' else ['False', 'True']

    # For yes/no
    if correct.lower() in ('yes', 'no'):
        return ['Yes', 'No'] if correct.lower() == 'no' else ['No', 'Yes']

    # For multi-value answers like "2, 3"
    if ',' in correct:
        distractors = _multi_value_distractors(correct)
        if distractors:
            return distractors

    # For common mistakes in word problems
    # If answer is a number in word form, return numeric version
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    }
    if correct.lower() in word_to_num:
        num = word_to_num[correct.lower()]
        distractors.append(str(num + 1))
        distractors.append(str(num - 1))

    return distractors


def _fallback_distractor(correct, exclude=None):
    """Generate a fallback distractor when others fail.

    Args:
        correct: The correct answer (to avoid)
        exclude: Set of values to exclude
    """
    if exclude is None:
        exclude = set()

    # Common fallback: offer sequential options for numeric answers
    num = _parse_number(correct)
    if num is not None:
        for i in [1, 2, 3, 4, -1, -2, -3, -4]:
            val = num + i
            formatted = str(int(val)) if val == int(val) else f"{val:.2f}"
            if formatted not in exclude and formatted != correct:
                return formatted

    # Fallback for text answers: try simple variants
    fallbacks = ['0', 'false', 'False', 'no', 'No', '1', 'unknown']
    for fb in fallbacks:
        if fb not in exclude and fb != correct:
            return fb

    # Last resort: return something unique
    return f"option_{random.randint(1000, 9999)}"


def insert_distractors(question_data):
    """Add computed distractors to a question dict.

    If the question already has options, replace them with computed ones.
    If it's MCQ type but has no options, generate them.
    """
    import re
    LETTER_PREFIX_RE = re.compile(r'^[A-Da-d][).\s]+\s*')

    q_type = question_data.get('question_type', 'mcq')
    if q_type != 'mcq':
        return question_data

    correct = question_data.get('correct_answer', '')
    if not correct:
        return question_data

    # Strip any existing letter prefix from correct answer
    correct = LETTER_PREFIX_RE.sub('', correct).strip()

    # Compute new distractors
    computed = compute_distractors(correct, num_options=4)

    # Build options: put correct at random position
    correct_index = random.randint(0, 3)
    options = []

    for i in range(4):
        if i == correct_index:
            options.append(correct)
        else:
            if computed:
                options.append(computed.pop(0))
            else:
                options.append(_fallback_distractor(correct))

    question_data['options'] = options

    # Update correct_answer to include letter (A/B/C/D)
    letters = ['A', 'B', 'C', 'D']
    question_data['correct_answer'] = f"{letters[correct_index]}) {correct}"

    return question_data
