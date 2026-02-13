"""Post-generation question validation — ported from kidtutor + math verifier.

15 rules that catch bad LLM output before it reaches the student.
Returns (is_valid, rejection_reason) tuple.
"""
import ast
import re

MAX_ANSWER_LENGTH = 200
MIN_QUESTION_LENGTH = 10
MIN_CHOICES = 3

PLACEHOLDER_ANSWERS = {'', '?', '...', 'n/a', 'none', 'null', 'tbd', 'unknown'}

PLACEHOLDER_PATTERNS = ['[shows', '[image', '[picture', '[display', '[insert', '[x ', '[x>', '[x<']

BANNED_CHOICES = {
    'all of the above', 'none of the above',
    'all the above', 'none of these', 'all of these',
    'not enough information', 'cannot be determined',
    'not enough info', 'impossible to tell',
}

# Phrases that indicate the question requires seeing a physical object or image
# that the student can't see in a text-only interface
REQUIRES_VISUAL_PATTERNS = [
    'which is longer', 'which is shorter', 'which is taller', 'which is smaller',
    'which is heavier', 'which is lighter',
    'look at the', 'looking at the', 'shown in the', 'shown above',
    'in the picture', 'in the image', 'in the diagram', 'in the figure',
    'the picture shows', 'the image shows', 'the diagram shows',
    'use the graph', 'use the chart', 'use the table',
    'from the graph', 'from the chart', 'from the table',
    'read the graph', 'read the chart',
    'the bar graph', 'the pictograph', 'the tally chart',
]

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
    question = str(q_data.get('question') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()
    choices = q_data.get('options') or []
    if not isinstance(choices, list):
        choices = []

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
        # Strip letter prefixes from answer before comparing (e.g., "A) Paris" → "Paris")
        answer_stripped = LETTER_PREFIX_RE.sub('', answer).strip()
        answer_lower = answer_stripped.lower()
        # Strip letter prefixes from choices before comparing (e.g., "A) 12" → "12")
        choice_lowers = [LETTER_PREFIX_RE.sub('', c).strip().lower() for c in choices]
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
    # Strip MCQ letter prefix (e.g., "C) x > -3" → "x > -3") before checking
    answer_text = LETTER_PREFIX_RE.sub('', answer).strip()
    if len(answer_text) > 1 and not _answer_in_question_is_ok(question, answer_text, choices):
        q_lower = question.lower()
        if answer_text.lower() in q_lower:
            return False, 'Answer given away in question text'

    # Rule 6: No placeholder text
    q_lower = question.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in q_lower:
            return False, f'Placeholder text found: "{pattern}"'

    # Rule 6b: No questions requiring unseen visuals/physical objects
    for pattern in REQUIRES_VISUAL_PATTERNS:
        if pattern in q_lower:
            return False, f'Question requires visual context: "{pattern}"'

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

    # Rule 14: Explanation vs answer cross-check
    expl_ok, expl_reason = verify_explanation_vs_answer(q_data)
    if not expl_ok:
        return False, expl_reason

    # Rule 15: Verify arithmetic expressions within explanation
    arith_ok, arith_reason = verify_explanation_arithmetic(q_data)
    if not arith_ok:
        return False, arith_reason

    # Rule 16: Reject text descriptions of visual diagrams
    desc_ok, desc_reason = _check_visual_descriptions(question, choices)
    if not desc_ok:
        return False, desc_reason

    # Rule 17: Reject "graph/draw/sketch/plot" imperatives
    draw_ok, draw_reason = _check_draw_imperatives(question)
    if not draw_ok:
        return False, draw_reason

    # Rule 18: Distractor quality check (MCQ only) — reject nonsensical options
    dist_ok, dist_reason = verify_distractor_quality(q_data)
    if not dist_ok:
        return False, dist_reason

    # Rule 19: Check for multiple correct answers in context
    # Example: "Which is even: 13, 24, 37, 48, 59?" has TWO correct answers (24 AND 48)
    multi_ok, multi_reason = _check_multiple_correct_answers(question, answer, choices)
    if not multi_ok:
        return False, multi_reason

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

    # Normalize unicode math operators
    q = q.replace('×', '*').replace('÷', '/')

    # Skip comparison questions — they pick between values, not compute
    if any(w in q for w in ('which is bigger', 'which is larger',
                             'which is smaller', 'which is greater',
                             'which is less', 'which is more',
                             'compare', 'order')):
        return None

    # --- Direct arithmetic expressions ---
    # "5 + 3", "15 - 7", "5 + 3 + 2", "8 * 4", "12 / 3", "3 × 4 ÷ 2"
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

    # --- Multi-step natural language operations ---
    # "multiply A by B and/then divide by C" → (A * B) / C
    m = re.search(
        r'multipl(?:y|ying)\s+(\d+)\s+by\s+(\d+)'
        r'.*?divid(?:e|ing)\s+(?:(?:the\s+result|it|that)\s+)?by\s+(\d+)',
        q,
    )
    if m and int(m.group(3)) != 0:
        return (int(m.group(1)) * int(m.group(2))) / int(m.group(3))

    # "divide A by B and/then multiply by C" → (A / B) * C
    m = re.search(
        r'divid(?:e|ing)\s+(\d+)\s+by\s+(\d+)'
        r'.*?multipl(?:y|ying)\s+(?:(?:the\s+result|it|that)\s+)?by\s+(\d+)',
        q,
    )
    if m and int(m.group(2)) != 0:
        return (int(m.group(1)) / int(m.group(2))) * int(m.group(3))

    # "multiply/multiplying A by B" → A * B (single step)
    m = re.search(r'multipl(?:y|ying)\s+(\d+)\s+by\s+(\d+)', q)
    if m:
        return int(m.group(1)) * int(m.group(2))

    # "divide/dividing A by B" → A / B (single step)
    m = re.search(r'divid(?:e|ing)\s+(\d+)\s+by\s+(\d+)', q)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2))

    # "product of A and B" → A * B
    m = re.search(r'product\s+of\s+(\d+)\s+and\s+(\d+)', q)
    if m:
        return int(m.group(1)) * int(m.group(2))

    # "sum of A, B, and C" → A + B + C (comma-separated three+ addends)
    m = re.search(r'sum\s+of\s+([\d,\s]+and\s+\d+)', q)
    if m:
        nums = re.findall(r'\d+', m.group(1))
        if len(nums) >= 2:
            return sum(int(n) for n in nums)

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

    # --- Word problem: subtraction ---
    # "has/have N ... eats/gives/loses/gave/spent M"
    m = re.search(
        r'(?:has|have|had|holds|starts?\s+with|began?\s+with|picks?\s+up|'
        r'bought|collects?|finds?|found|carries?|bakes?|makes?|owns?)\s+(\d+)'
        r'.*?'
        r'(?:eats?|ate|gives?\s+away|gives?|gave|loses?|lost|spent|spends?|'
        r'breaks?|broke|drops?|dropped|took\s+away|takes?\s+away|'
        r'used|uses?|removes?|removed|throws?\s+away|threw\s+away|'
        r'sold|sells?|shares?|shared|lends?|lent|returns?|returned)\s+(\d+)',
        q
    )
    if m:
        return int(m.group(1)) - int(m.group(2))

    # --- Word problem: addition ---
    # "has/have N ... gets/receives/finds/bought M more"
    m = re.search(
        r'(?:has|have|had|holds|starts?\s+with|began?\s+with|owns?)\s+(\d+)'
        r'.*?'
        r'(?:gets?|receives?|finds?|found|picks?\s+up|bought|buys?|'
        r'collects?|collected|earns?|earned|wins?|won|adds?|added|'
        r'gets?\s+back|more)\s+(\d+)',
        q
    )
    if m:
        return int(m.group(1)) + int(m.group(2))

    # --- Word problem: "N things, M verb away" (reverse order) ---
    # "There are N birds. M fly away."
    m = re.search(
        r'(?:there\s+(?:are|were|is)|(\w+)\s+(?:has|have|had))\s+(\d+)'
        r'.*?'
        r'(\d+)\s+(?:fly\s+away|flew\s+away|walk\s+away|walked\s+away|'
        r'ran\s+away|run\s+away|leave|left|fall\s+off|fell\s+off|'
        r'go\s+away|went\s+away|are\s+taken|were\s+taken|'
        r'are\s+eaten|were\s+eaten|are\s+removed|were\s+removed|'
        r'pop|popped|burst|break|broke)',
        q
    )
    if m:
        total = int(m.group(2))
        removed = int(m.group(3))
        return total - removed

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


def _extract_explanation_results(explanation):
    """Extract all computed results from an explanation — both math notation and natural language.

    Returns a list of floats in order of appearance. The last is typically the final answer.
    Handles:
      - "= N" patterns: "5 + 3 = 8"
      - "to get N", "to obtain N", "giving N", "leaving N"
      - "which is N", "the result is N", "the answer is N"
      - "you get N", "equals N", "we get N"
    """
    results = []

    # Math notation: "= N"
    for m in re.finditer(r'=\s*(\d+(?:\.\d+)?)', explanation):
        results.append((m.start(), float(m.group(1))))

    # Natural language result patterns
    nl_patterns = [
        r'to\s+get\s+(\d+(?:\.\d+)?)',
        r'to\s+obtain\s+(\d+(?:\.\d+)?)',
        r'(?:which|that)\s+is\s+(\d+(?:\.\d+)?)',
        r'the\s+(?:result|answer)\s+is\s+(\d+(?:\.\d+)?)',
        r'(?:giving|leaves?|leaving)\s+(\d+(?:\.\d+)?)',
        r'(?:you|we)\s+get\s+(\d+(?:\.\d+)?)',
        r'equals?\s+(\d+(?:\.\d+)?)',
    ]
    for pat in nl_patterns:
        for m in re.finditer(pat, explanation, re.IGNORECASE):
            results.append((m.start(), float(m.group(1))))

    # Sort by position in text and return just the values
    results.sort(key=lambda x: x[0])
    return [v for _, v in results]


def verify_explanation_vs_answer(q_data):
    """Cross-check: does the explanation's own math agree with the stated answer?

    Catches cases where the LLM sets correct_answer="3" but the explanation
    correctly computes "9 - 5 = 4". Also catches natural language explanations
    like "divide 12 by 2 to obtain the result, which is 6" vs answer "12".

    Returns (is_valid, reason).
    """
    explanation = (q_data.get('explanation') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()
    options = q_data.get('options') or []

    if not explanation:
        return True, ''

    # Resolve the stated answer to a number
    resolved = _resolve_answer_text(answer, options)
    stated_num = _parse_numeric(resolved)
    if stated_num is None:
        return True, ''  # Not numeric

    # Extract all results from the explanation (math and natural language)
    results = _extract_explanation_results(explanation)
    if results:
        final_computed = results[-1]
        if abs(final_computed - stated_num) > 0.01:
            return False, (
                f'Explanation contradicts answer: explanation computes '
                f'{int(final_computed) if final_computed == int(final_computed) else final_computed}, '
                f'but stated answer is {resolved}'
            )

    return True, ''


def verify_explanation_arithmetic(q_data):
    """Rule 15: Verify that arithmetic expressions within the explanation are correct.

    Catches cases like "4 - 2 = 3" where the LLM's own arithmetic is wrong,
    even when the stated answer and explanation's final result agree.

    Returns (is_valid, reason).
    """
    explanation = (q_data.get('explanation') or '').strip()
    if not explanation:
        return True, ''

    # Normalize unicode dashes
    explanation = _DASH_RE.sub('-', explanation)

    # Find all "A op B [op C ...] = N" patterns
    # e.g. "4 - 2 = 3", "5 + 3 + 2 = 10", "6 * 4 = 24"
    pattern = r'(\d+(?:\s*[+\-*/×÷]\s*\d+)+)\s*=\s*(\d+(?:\.\d+)?)'

    for match in re.finditer(pattern, explanation):
        expr_str = match.group(1)
        stated_result = float(match.group(2))

        # Normalize unicode operators
        normalized = expr_str.replace('×', '*').replace('÷', '/')

        computed = _safe_eval_expr(normalized)
        if computed is not None and abs(computed - stated_result) > 0.01:
            computed_display = int(computed) if computed == int(computed) else computed
            stated_display = int(stated_result) if stated_result == int(stated_result) else stated_result
            return False, (
                f'Explanation arithmetic error: {expr_str.strip()} = '
                f'{computed_display}, not {stated_display}'
            )

    return True, ''


def _answer_in_question_is_ok(question, answer, choices):
    """Check if answer appearing in question is an expected pattern.

    Math expressions, comparisons, and classification questions
    naturally contain the answer in the question text.
    answer should already be stripped of MCQ letter prefix.
    """
    q_lower = question.lower()
    a_lower = answer.lower().strip()

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

    # REJECT: Answer in brackets [x > -5] is placeholder format (local generator bug)
    if '[' in question and ']' in question and a_lower in question:
        return False

    # "What/which" identification questions (but NOT "which [inequality|expression] does")
    # "Which is the capital of..." → OK to have answer
    # "Which inequality does this represent? [x > -5]" → NOT OK (has bracket answer)
    if q_lower.startswith(('what ', 'which ')):
        # Allow ONLY if it's a specific identification pattern
        # "which is", "which of", "what is"
        if any(pattern in q_lower for pattern in ('which is ', 'which of ', 'what is ')):
            return True
        # But NOT generic "which [expression]" patterns
        if any(pattern in q_lower for pattern in ('which inequality', 'which equation',
                                                     'which expression')):
            return False
        return True

    # Single character answers (letters, digits) are too common to flag
    if len(answer) <= 1:
        return True

    return False


# ---------------------------------------------------------------------------
# Rule 19: Multiple correct answers check
# ---------------------------------------------------------------------------


def _check_multiple_correct_answers(question, answer, choices):
    """Rule 19: Reject questions where context allows multiple correct answers.

    Examples:
    - "Which is even: 13, 24, 37, 48, 59?" → Both 24 AND 48 are correct (ambiguous!)
    - "Name a color: red, blue, green" → Any color mentioned is correct (ambiguous!)

    Returns (is_valid, reason).
    """
    q_lower = question.lower()
    answer_text = LETTER_PREFIX_RE.sub('', answer).strip()

    # Extract all numbers mentioned in the question using regex
    # Look for sequences like "24, 37, 48" or "13, 24, 37"
    number_pattern = r'\d+'
    numbers_in_question = [int(m) for m in re.findall(number_pattern, question)]

    if not numbers_in_question:
        return True, ''  # No numbers mentioned, can't have multiple answers

    # Try to parse the correct answer as a number
    try:
        correct_num = int(re.search(r'\d+', answer_text).group()) if re.search(r'\d+', answer_text) else None
    except (ValueError, AttributeError):
        return True, ''  # Answer not numeric, skip this check

    if correct_num is None:
        return True, ''

    # Check if question contains "which is", "which are", "name", "list" - all suggest multiple possible answers
    ambiguous_phrases = [
        'which is even', 'which is odd', 'which is prime',
        'which is divisible', 'which is a multiple',
        'which of these', 'which one',
        'what color', 'what number', 'what digit',
        'name', 'list', 'find all'
    ]

    has_ambiguous_phrasing = any(phrase in q_lower for phrase in ambiguous_phrases)

    if not has_ambiguous_phrasing:
        return True, ''

    # Count how many numbers in the question satisfy the same property as the answer
    # For "even" questions: count even numbers
    # For "odd" questions: count odd numbers
    # For "divisible by X" questions: count numbers divisible by X

    if any(word in q_lower for word in ['even']):
        matching_count = sum(1 for n in numbers_in_question if n % 2 == 0)
    elif any(word in q_lower for word in ['odd']):
        matching_count = sum(1 for n in numbers_in_question if n % 2 == 1)
    elif 'prime' in q_lower:
        # Simplified prime check
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True
        matching_count = sum(1 for n in numbers_in_question if is_prime(n))
    elif 'divisible' in q_lower:
        # Extract divisor from question like "divisible by 3"
        m = re.search(r'divisible by (\d+)', q_lower)
        if m:
            divisor = int(m.group(1))
            matching_count = sum(1 for n in numbers_in_question if n % divisor == 0)
        else:
            return True, ''
    else:
        # Can't determine the property, allow it
        return True, ''

    # If more than one number matches the property, it's ambiguous
    if matching_count > 1:
        matching_numbers = [
            n for n in numbers_in_question
            if (any(word in q_lower for word in ['even']) and n % 2 == 0) or
               (any(word in q_lower for word in ['odd']) and n % 2 == 1)
        ]
        return False, (
            f'Rule 19: Multiple correct answers in context. '
            f'Question mentions {matching_count} numbers that satisfy the condition '
            f'(found {matching_numbers}), but only one should match.'
        )

    return True, ''


# ---------------------------------------------------------------------------
# Rule 18: Distractor quality check
# ---------------------------------------------------------------------------


def verify_distractor_quality(q_data):
    """Rule 18: Reject MCQ questions with nonsensical distractors.

    Detects:
    - Type mismatches (Hebrew answer + English fallbacks)
    - Multiple hardcoded fallbacks (0, false, False, etc.)
    - Semantic incoherence

    Returns (is_valid, reason).
    """
    question = q_data.get('question', '')
    answer = q_data.get('correct_answer', '')
    choices = q_data.get('options', [])
    q_type = q_data.get('question_type', 'mcq')

    if q_type != 'mcq' or not choices:
        return True, ''

    # Strip letter prefixes from answer
    answer_text = LETTER_PREFIX_RE.sub('', answer).strip()

    # Known fallback values that indicate poor distractor generation
    FALLBACK_SET = {
        '0', '1', 'false', 'False', 'true', 'True',
        'no', 'No', 'yes', 'Yes', 'unknown', 'unknown'
    }

    # Count fallbacks in options
    fallback_count = sum(1 for opt in choices if opt.strip() in FALLBACK_SET)

    # Allow fallbacks if this is explicitly a boolean question
    is_boolean_question = any(phrase in question.lower() for phrase in [
        'true or false', 'is it true', 'is it false', 'yes or no',
        'true/false', 'yes/no'
    ])
    if is_boolean_question and fallback_count <= 2:
        return True, ''

    # Reject if 2+ fallbacks used inappropriately
    if fallback_count >= 2:
        return False, (
            f'Rule 18: Too many nonsensical distractors ({fallback_count}). '
            'Unable to generate meaningful options.'
        )

    # Detect type mismatches (complex answer + simple fallbacks)
    has_hebrew = bool(re.search(r'[\u0590-\u05FF]', answer_text))
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', answer_text))
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', answer_text))
    has_latex = bool(re.search(r'\\[a-z]+\{', answer_text))
    has_math_symbols = any(s in answer_text for s in ['≥', '≤', '÷', '×', '∑', '∫'])

    if (has_hebrew or has_arabic or has_chinese or has_latex or has_math_symbols) and fallback_count > 0:
        return False, (
            'Rule 18: Type mismatch — complex answer with generic fallback distractors'
        )

    return True, ''


# ---------------------------------------------------------------------------
# Rules 16-17: Visual description and draw-imperative checks
# ---------------------------------------------------------------------------

# Text descriptions of visual diagrams — student can't see these
VISUAL_DESCRIPTION_PATTERNS = [
    'open circle at', 'closed circle at', 'filled circle at',
    'shading to the right', 'shading to the left',
    'arrow pointing', 'number line shows', 'graph shows',
    'the line passes through', 'the curve passes through',
    'dashed line', 'solid line at', 'dotted line',
]

# Imperatives asking students to produce visual output
DRAW_IMPERATIVE_PATTERNS = [
    'graph it', 'graph the', 'draw the', 'draw a',
    'sketch the', 'sketch a', 'plot the', 'plot a',
    'then graph', 'and graph', 'then draw', 'and draw',
    'then sketch', 'then plot',
]


def _check_visual_descriptions(question, choices):
    """Rule 16: Reject questions/options that describe visuals in text."""
    q_lower = question.lower()
    for pattern in VISUAL_DESCRIPTION_PATTERNS:
        if pattern in q_lower:
            return False, f'Question describes visual in text: "{pattern}"'

    # Also check MCQ options — text descriptions of diagrams as choices
    for choice in choices:
        c_lower = choice.lower()
        for pattern in VISUAL_DESCRIPTION_PATTERNS:
            if pattern in c_lower:
                return False, f'Choice describes visual in text: "{pattern}"'

    return True, ''


def _check_draw_imperatives(question):
    """Rule 17: Reject questions asking students to graph/draw/sketch/plot."""
    q_lower = question.lower()
    for pattern in DRAW_IMPERATIVE_PATTERNS:
        if pattern in q_lower:
            return False, f'Question asks student to produce visual: "{pattern}"'
    return True, ''
