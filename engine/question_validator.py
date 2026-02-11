"""Post-generation question validation — ported from kidtutor + math verifier.

13 rules that catch bad LLM output before it reaches the student.
Returns (is_valid, rejection_reason) tuple.
"""
import ast
import re

MAX_ANSWER_LENGTH = 200
MIN_QUESTION_LENGTH = 10
MIN_CHOICES = 3

PLACEHOLDER_ANSWERS = {'', '?', '...', 'n/a', 'none', 'null', 'tbd', 'unknown'}

PLACEHOLDER_PATTERNS = ['[shows', '[image', '[picture', '[display', '[insert']

BANNED_CHOICES = {
    'all of the above', 'none of the above',
    'all the above', 'none of these', 'all of these',
}

LETTER_PREFIX_RE = re.compile(r'^[A-Da-d][).\s]+\s*')

IMPERATIVE_VERBS = {
    'simplify', 'solve', 'calculate', 'count', 'find', 'convert',
    'round', 'name', 'list', 'spell', 'write', 'read', 'say',
    'translate', 'match', 'determine', 'evaluate', 'compute',
    'identify', 'explain', 'describe', 'compare',
}

# Patterns where answer appearing in question is expected
MATH_EXPRESSION_RE = re.compile(
    r'[\d\s+\-*/×÷=<>()]+', re.UNICODE
)


def validate_question(q_data, node_description=''):
    """Validate a generated question dict.

    Args:
        q_data: dict with keys: question, correct_answer, options (optional)
        node_description: curriculum node description for context

    Returns:
        (is_valid, reason) — reason is '' if valid.
    """
    question = (q_data.get('question') or '').strip()
    answer = (q_data.get('correct_answer') or '').strip()
    choices = q_data.get('options') or []

    # Rule 1: Question text minimum length
    if len(question) < MIN_QUESTION_LENGTH:
        return False, f'Question too short ({len(question)} chars, min {MIN_QUESTION_LENGTH})'

    # Rule 2: Answer not empty or placeholder
    if answer.lower() in PLACEHOLDER_ANSWERS:
        return False, f'Answer is empty or placeholder: "{answer}"'

    # Rule 3: Choices must be unique (if provided) — strip letter prefixes
    if choices:
        normalized = [LETTER_PREFIX_RE.sub('', c).strip().lower() for c in choices]
        if len(normalized) != len(set(normalized)):
            return False, 'Duplicate choices'

    # Rule 4: Correct answer must be among choices (if provided)
    if choices:
        answer_lower = answer.lower().strip()
        choice_lowers = [c.strip().lower() for c in choices]
        # Also check just the letter (A, B, C, D)
        letter_match = answer_lower in ('a', 'b', 'c', 'd')
        text_match = answer_lower in choice_lowers
        # Check if answer letter corresponds to a choice
        idx_match = False
        if len(answer_lower) == 1 and answer_lower in 'abcd':
            idx = ord(answer_lower) - ord('a')
            idx_match = idx < len(choices)
        if not (text_match or letter_match or idx_match):
            return False, 'Correct answer not found in choices'

    # Rule 5: Answer not given away in question text
    if len(answer) > 1 and not _answer_in_question_is_ok(question, answer, choices):
        q_lower = question.lower()
        a_lower = answer.lower()
        if a_lower in q_lower:
            return False, 'Answer given away in question text'

    # Rule 6: No placeholder text
    q_lower = question.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in q_lower:
            return False, f'Placeholder text found: "{pattern}"'

    # Rule 7: Answer max length
    if len(answer) > MAX_ANSWER_LENGTH:
        return False, f'Answer too long ({len(answer)} chars, max {MAX_ANSWER_LENGTH})'

    # Rule 8: No HTML/markdown artifacts
    if '</' in question or '```' in question:
        return False, 'HTML or markdown artifacts in question'
    if '</' in answer or '```' in answer:
        return False, 'HTML or markdown artifacts in answer'

    # Rule 9: Minimum 3 choices (if choices provided)
    if choices and len(choices) < MIN_CHOICES:
        return False, f'Too few choices ({len(choices)}, min {MIN_CHOICES})'

    # Rule 10: Answer length bias prevention
    if choices:
        distractor_lens = [len(c.strip()) for c in choices if c.strip().lower() != answer.lower()]
        if distractor_lens:
            avg_distractor = sum(distractor_lens) / len(distractor_lens)
            max_distractor = max(distractor_lens)
            if len(answer) > avg_distractor * 3 and len(answer) > max_distractor + 15:
                return False, 'Answer much longer than distractors (length bias)'

    # Rule 11: No "all/none of the above" choices — strip letter prefixes
    if choices:
        for c in choices:
            stripped = LETTER_PREFIX_RE.sub('', c).strip().lower()
            if stripped in BANNED_CHOICES or c.strip().lower() in BANNED_CHOICES:
                return False, f'Banned choice: "{c.strip()}"'

    # Rule 12: Question must have punctuation, blank, or imperative verb
    has_punctuation = bool(re.search(r'[?:.]', question))
    has_blank = '__' in question
    first_word = question.split()[0].lower().rstrip(':') if question.split() else ''
    has_imperative = first_word in IMPERATIVE_VERBS
    if not (has_punctuation or has_blank or has_imperative):
        return False, 'Question lacks punctuation or imperative verb'

    # Rule 13: Mathematical answer verification
    math_ok, math_reason = verify_math_answer(q_data)
    if not math_ok:
        return False, math_reason

    return True, ''


# ---------------------------------------------------------------------------
# Rule 13 helpers: Mathematical answer verification
# ---------------------------------------------------------------------------

def _safe_eval_expr(expr):
    """Safely evaluate a simple arithmetic expression using AST.

    Only allows integer/float literals and +, -, *, / operators.
    Returns a number or None if the expression is unsafe or invalid.
    """
    allowed_chars = set('0123456789+-*/ .')
    if not all(c in allowed_chars for c in expr):
        return None
    try:
        tree = ast.parse(expr.strip(), mode='eval')
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp)):
            continue
        if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub)):
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            continue
        return None  # disallowed node type
    try:
        return eval(compile(tree, '<expr>', 'eval'))
    except (ZeroDivisionError, OverflowError):
        return None


# Unicode dash variants: hyphen-minus, minus sign, en-dash, em-dash
_DASH_RE = re.compile(r'[−–—]')


def _try_compute_answer(question_text):
    """Try to extract and compute the mathematical answer from a question.

    Returns a number if the question contains a verifiable expression,
    or None if the question can't be parsed (benefit of the doubt).
    """
    q = _DASH_RE.sub('-', question_text.lower().strip())

    # Skip comparison questions — they pick between values, not compute
    if any(w in q for w in ('which is bigger', 'which is larger',
                             'which is smaller', 'which is greater',
                             'which is less', 'which is more',
                             'compare', 'order')):
        return None

    # --- Direct arithmetic expressions ---
    # "5 + 3", "15 - 7", "5 + 3 + 2", "8 * 4", "12 / 3"
    expr_match = re.search(r'(\d+(?:\s*[+\-*/]\s*\d+)+)', q)
    if expr_match:
        result = _safe_eval_expr(expr_match.group(1))
        if result is not None:
            return result

    # --- Word-based operations ---
    # "A plus B [plus C]"
    m = re.search(r'(\d+)\s+plus\s+(\d+)(?:\s+plus\s+(\d+))?', q)
    if m:
        nums = [int(g) for g in m.groups() if g is not None]
        return sum(nums)

    # "A minus B"
    m = re.search(r'(\d+)\s+minus\s+(\d+)', q)
    if m:
        return int(m.group(1)) - int(m.group(2))

    # "A times B"
    m = re.search(r'(\d+)\s+times\s+(\d+)', q)
    if m:
        return int(m.group(1)) * int(m.group(2))

    # "A divided by B"
    m = re.search(r'(\d+)\s+divided\s+by\s+(\d+)', q)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2))

    # --- Phrased patterns ---
    # "N more than M" → M + N
    m = re.search(r'(\d+)\s+more\s+than\s+(\d+)', q)
    if m:
        return int(m.group(2)) + int(m.group(1))

    # "N less than M" → M - N
    m = re.search(r'(\d+)\s+less\s+than\s+(\d+)', q)
    if m:
        return int(m.group(2)) - int(m.group(1))

    # "subtract A from B" → B - A
    m = re.search(r'subtract\s+(\d+)\s+from\s+(\d+)', q)
    if m:
        return int(m.group(2)) - int(m.group(1))

    # "add A and B" / "sum of A and B"
    m = re.search(r'(?:add|sum\s+of)\s+(\d+)\s+and\s+(\d+)', q)
    if m:
        return int(m.group(1)) + int(m.group(2))

    # "difference between/of A and B" → |A - B|
    m = re.search(r'difference\s+(?:between|of)\s+(\d+)\s+and\s+(\d+)', q)
    if m:
        return abs(int(m.group(1)) - int(m.group(2)))

    # --- Missing number equations ---
    # "__ + A = B" or "? + A = B" → B - A
    m = re.search(r'(?:_+|\?)\s*\+\s*(\d+)\s*=\s*(\d+)', q)
    if m:
        return int(m.group(2)) - int(m.group(1))

    # "A + __ = B" or "A + ? = B" → B - A
    m = re.search(r'(\d+)\s*\+\s*(?:_+|\?)\s*=\s*(\d+)', q)
    if m:
        return int(m.group(2)) - int(m.group(1))

    # "__ - A = B" → B + A
    m = re.search(r'(?:_+|\?)\s*-\s*(\d+)\s*=\s*(\d+)', q)
    if m:
        return int(m.group(2)) + int(m.group(1))

    # "A - __ = B" → A - B
    m = re.search(r'(\d+)\s*-\s*(?:_+|\?)\s*=\s*(\d+)', q)
    if m:
        return int(m.group(1)) - int(m.group(2))

    # --- "10 more/less" patterns ---
    # "What is 10 more than 45?" → 45 + 10 = 55  (already caught above)
    # "What is 10 less than 45?" → 45 - 10 = 35  (already caught above)

    return None  # Can't determine — skip verification


def _resolve_answer_text(answer, options):
    """Resolve an MCQ answer to its actual text value.

    Handles: "D) 9" → "9", "D" → options[3] text, "9" → "9"
    """
    if not answer:
        return answer

    # Strip letter prefix: "D) 9" → "9", "B. cat" → "cat"
    stripped = LETTER_PREFIX_RE.sub('', answer).strip()
    if stripped and stripped != answer.strip():
        return stripped

    # If answer is just a letter (A-D), look it up in options
    if options and len(answer.strip()) == 1 and answer.strip().upper() in 'ABCD':
        idx = ord(answer.strip().upper()) - ord('A')
        if idx < len(options):
            return LETTER_PREFIX_RE.sub('', options[idx]).strip()

    return answer.strip()


def _parse_numeric(text):
    """Try to parse a string as a number. Returns float or None."""
    text = text.strip()
    try:
        if '/' in text and text.count('/') == 1:
            num, den = text.split('/')
            d = float(den)
            return float(num) / d if d != 0 else None
        return float(text)
    except (ValueError, ZeroDivisionError):
        return None


def verify_math_answer(q_data):
    """Independently verify the mathematical correctness of a question's answer.

    Returns (is_valid, reason).
    - (True, '') if answer is correct or can't be verified.
    - (False, reason) if computed answer differs from stated answer.
    """
    question = (q_data.get('question') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()
    options = q_data.get('options') or []

    # Resolve MCQ letter to actual answer text
    resolved = _resolve_answer_text(answer, options)

    # Parse the stated answer as a number
    stated_num = _parse_numeric(resolved)
    if stated_num is None:
        return True, ''  # Not a numeric answer — can't verify

    # Try to compute the correct answer from the question
    computed = _try_compute_answer(question)
    if computed is None:
        return True, ''  # Can't extract expression — skip

    # Compare (allow small floating point tolerance)
    if abs(computed - stated_num) > 0.01:
        return False, (
            f'Math verification failed: question computes to '
            f'{int(computed) if computed == int(computed) else computed}, '
            f'but stated answer is {resolved}'
        )

    return True, ''


def _answer_in_question_is_ok(question, answer, choices):
    """Check if answer appearing in question is an expected pattern.

    Math expressions, comparisons, and classification questions
    naturally contain the answer in the question text.
    """
    q_lower = question.lower()
    a_lower = answer.lower()

    if a_lower not in q_lower:
        return True  # answer not in question, no issue

    # Math expressions: "What is 86 - 43?" answer="43" is fine
    if re.search(r'what is\s+[\d\s+\-*/×÷.]+', q_lower):
        return True

    # Comparison: "Which is bigger: 2/5 or 4/5?" answer="4/5"
    if any(w in q_lower for w in ('which is bigger', 'which is larger',
                                   'which is smaller', 'which is greater',
                                   'which is less')):
        return True

    # Classification: "Is X a Y, Z, or W?" — answer naturally in choices
    if q_lower.startswith(('is ', 'are ', 'does ', 'do ', 'can ', 'will ')):
        return True

    # "What/which" identification questions
    if q_lower.startswith(('what ', 'which ')):
        return True

    # Single character answers (letters, digits) are too common to flag
    if len(answer) <= 1:
        return True

    return False
