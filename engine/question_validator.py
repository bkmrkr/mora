"""Post-generation question validation — ported from kidtutor.

11 rules that catch bad LLM output before it reaches the student.
Returns (is_valid, rejection_reason) tuple.
"""
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
