"""Post-generation question validation.

5 structural rules + simplified math verification.
Validates structure only — factual correctness is the LLM's responsibility.

Returns (is_valid, rejection_reason) tuple.
"""
import ast
import re

MAX_ANSWER_LENGTH = 200
MIN_QUESTION_LENGTH = 10

PLACEHOLDER_ANSWERS = {'', '?', '...', 'n/a', 'none', 'null', 'tbd', 'unknown'}

BANNED_CHOICES = {
    'all of the above', 'none of the above',
    'all the above', 'none of these', 'all of these',
    'not enough information', 'cannot be determined',
}

VISUAL_PATTERNS = [
    'look at the', 'in the picture', 'in the image', 'in the diagram',
    'shown in the', 'shown above', 'the picture shows', 'the image shows',
    'use the graph', 'use the chart', 'use the table',
    'from the graph', 'from the chart',
    'graph it', 'graph the', 'draw the', 'draw a',
    'sketch the', 'sketch a', 'plot the', 'plot a',
    '[shows', '[image', '[picture', '[display', '[insert',
]


def validate_question(q_data, node_description=''):
    """Validate a generated question dict.

    5 structural rules + math verification:
      1. Question text minimum length
      2. Answer not empty/placeholder, not too long
      3. MCQ: 4 unique options, correct answer present, no banned choices
      4. No HTML/markdown artifacts
      5. No visual references

    Plus: math answer verification and explanation cross-check.

    Returns (is_valid, reason) — reason is '' if valid.
    """
    question = str(q_data.get('question') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()
    choices = q_data.get('options') or []
    if not isinstance(choices, list):
        choices = []

    # Rule 1: Question text minimum length
    if len(question) < MIN_QUESTION_LENGTH:
        return False, f'Question too short ({len(question)} chars)'

    # Rule 2: Answer validation
    if answer.lower() in PLACEHOLDER_ANSWERS:
        return False, f'Answer is empty or placeholder: "{answer}"'
    if len(answer) > MAX_ANSWER_LENGTH:
        return False, f'Answer too long ({len(answer)} chars)'

    # Rule 3: MCQ options validation
    if choices:
        if len(choices) < 3:
            return False, f'Too few choices ({len(choices)})'

        # Unique options
        normalized = [c.strip().lower() for c in choices]
        if len(normalized) != len(set(normalized)):
            return False, 'Duplicate choices'

        # Correct answer must be in options
        answer_lower = answer.strip().lower()
        choice_lowers = [c.strip().lower() for c in choices]
        if answer_lower not in choice_lowers:
            return False, 'Correct answer not found in choices'

        # No banned choices
        for c in choices:
            if c.strip().lower() in BANNED_CHOICES:
                return False, f'Banned choice: "{c.strip()}"'

    # Rule 4: No HTML/markdown artifacts
    if '</' in question or '```' in question:
        return False, 'HTML or markdown artifacts in question'
    if '</' in answer or '```' in answer:
        return False, 'HTML or markdown artifacts in answer'

    # Rule 5: No visual references
    q_lower = question.lower()
    for pattern in VISUAL_PATTERNS:
        if pattern in q_lower:
            return False, f'Question requires visual context: "{pattern}"'

    # Math verification (catches blatant arithmetic errors)
    math_ok, math_reason = verify_math_answer(q_data)
    if not math_ok:
        return False, math_reason

    expl_ok, expl_reason = verify_explanation_vs_answer(q_data)
    if not expl_ok:
        return False, expl_reason

    arith_ok, arith_reason = verify_explanation_arithmetic(q_data)
    if not arith_ok:
        return False, arith_reason

    return True, ''


# ---------------------------------------------------------------------------
# Math verification helpers
# ---------------------------------------------------------------------------

# Unicode dash variants
_DASH_RE = re.compile(r'[−–—]')


def _safe_eval_expr(expr):
    """Safely evaluate a simple arithmetic expression using AST.

    Only allows integer/float literals and +, -, *, / operators.
    Returns a number or None if unsafe/invalid.
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
        return None
    try:
        return eval(compile(tree, '<expr>', 'eval'))
    except (ZeroDivisionError, OverflowError):
        return None


def _try_compute_answer(question_text):
    """Try to extract and compute the answer from direct arithmetic in a question.

    Only handles explicit expressions like "5 + 3", "15 - 7", "8 * 4".
    Returns a number or None (benefit of the doubt).
    """
    q = _DASH_RE.sub('-', question_text.lower().strip())
    q = q.replace('×', '*').replace('÷', '/')

    # Skip comparison questions
    if any(w in q for w in ('which is bigger', 'which is larger',
                             'which is smaller', 'which is greater',
                             'which is less', 'compare', 'order')):
        return None

    # Direct arithmetic: "5 + 3", "15 - 7", "3 × 4 ÷ 2"
    expr_match = re.search(r'(\d+(?:\s*[+\-*/]\s*\d+)+)', q)
    if expr_match:
        result = _safe_eval_expr(expr_match.group(1))
        if result is not None:
            return result

    # Word-based: "A plus B", "A minus B", "A times B", "A divided by B"
    m = re.search(r'(\d+)\s+plus\s+(\d+)(?:\s+plus\s+(\d+))?', q)
    if m:
        nums = [int(g) for g in m.groups() if g is not None]
        return sum(nums)

    m = re.search(r'(\d+)\s+minus\s+(\d+)', q)
    if m:
        return int(m.group(1)) - int(m.group(2))

    m = re.search(r'(\d+)\s+times\s+(\d+)', q)
    if m:
        return int(m.group(1)) * int(m.group(2))

    m = re.search(r'(\d+)\s+divided\s+by\s+(\d+)', q)
    if m and int(m.group(2)) != 0:
        return int(m.group(1)) / int(m.group(2))

    return None


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
    """Verify mathematical correctness of a question's answer.

    Returns (is_valid, reason).
    """
    question = (q_data.get('question') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()

    stated_num = _parse_numeric(answer)
    if stated_num is None:
        return True, ''  # Not numeric — can't verify

    computed = _try_compute_answer(question)
    if computed is None:
        return True, ''  # Can't extract expression — skip

    if abs(computed - stated_num) > 0.01:
        return False, (
            f'Math verification failed: question computes to '
            f'{int(computed) if computed == int(computed) else computed}, '
            f'but stated answer is {answer}'
        )
    return True, ''


def _extract_explanation_results(explanation):
    """Extract all computed results from an explanation.

    Returns a list of floats in order of appearance.
    """
    results = []

    for m in re.finditer(r'=\s*(\d+(?:\.\d+)?)', explanation):
        results.append((m.start(), float(m.group(1))))

    nl_patterns = [
        r'to\s+get\s+(\d+(?:\.\d+)?)',
        r'(?:which|that)\s+is\s+(\d+(?:\.\d+)?)',
        r'the\s+(?:result|answer)\s+is\s+(\d+(?:\.\d+)?)',
        r'(?:giving|leaves?|leaving)\s+(\d+(?:\.\d+)?)',
        r'(?:you|we)\s+get\s+(\d+(?:\.\d+)?)',
        r'equals?\s+(\d+(?:\.\d+)?)',
    ]
    for pat in nl_patterns:
        for m in re.finditer(pat, explanation, re.IGNORECASE):
            results.append((m.start(), float(m.group(1))))

    results.sort(key=lambda x: x[0])
    return [v for _, v in results]


def verify_explanation_vs_answer(q_data):
    """Cross-check: does the explanation's math agree with the stated answer?

    Returns (is_valid, reason).
    """
    explanation = (q_data.get('explanation') or '').strip()
    answer = str(q_data.get('correct_answer') or '').strip()

    if not explanation:
        return True, ''

    stated_num = _parse_numeric(answer)
    if stated_num is None:
        return True, ''

    results = _extract_explanation_results(explanation)
    if results:
        final_computed = results[-1]
        if abs(final_computed - stated_num) > 0.01:
            return False, (
                f'Explanation contradicts answer: explanation computes '
                f'{int(final_computed) if final_computed == int(final_computed) else final_computed}, '
                f'but stated answer is {answer}'
            )
    return True, ''


def verify_explanation_arithmetic(q_data):
    """Verify that arithmetic expressions within the explanation are correct.

    Catches "4 - 2 = 3" where the LLM's own arithmetic is wrong.
    Returns (is_valid, reason).
    """
    explanation = (q_data.get('explanation') or '').strip()
    if not explanation:
        return True, ''

    explanation = _DASH_RE.sub('-', explanation)
    pattern = r'(\d+(?:\s*[+\-*/×÷]\s*\d+)+)\s*=\s*(\d+(?:\.\d+)?)'

    for match in re.finditer(pattern, explanation):
        expr_str = match.group(1)
        stated_result = float(match.group(2))
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
