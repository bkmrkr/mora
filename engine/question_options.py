"""Question generation options and constants."""
import html
import re

# MCQ option letter prefixes
MCQ_LETTERS = ['A', 'B', 'C', 'D']
MCQ_OPTION_FORMAT = '{letter}) {text}'

# Similarity detection threshold (0-1)
SIMILARITY_THRESHOLD = 0.7

# Question types
QUESTION_TYPE_MCQ = 'mcq'

# Generation limits
MAX_GENERATION_ATTEMPTS = 5  # Will be read from config, this is for reference


def sanitize_answer(text):
    """Sanitize and normalize answer text.

    - Removes letter prefixes (A), B), etc.)
    - Strips whitespace
    - Escapes HTML special characters

    Args:
        text: Raw answer text from LLM

    Returns:
        Sanitized answer string
    """
    if not text:
        return ""

    # Remove letter prefix if present (e.g., "A) 6" → "6", "A. 6" → "6")
    # Match: single letter A-D (or a-d), followed by ) or ., followed by optional whitespace
    cleaned = re.sub(r'^[A-Da-d][).]\s*', '', text).strip()

    # Escape HTML entities to prevent XSS
    escaped = html.escape(cleaned)

    return escaped


def create_placeholder_options(correct_answer, attempt_num=0):
    """Create placeholder MCQ options for validation.

    This generates four options: one with the correct answer, three placeholders.
    The placeholders are temporary and will be replaced with real distractors later.

    All options are sanitized to prevent XSS vulnerabilities.

    Args:
        correct_answer: The correct answer text (will be sanitized)
        attempt_num: Attempt number (used to make placeholders unique across retries)

    Returns:
        List of four option strings: ['A) correct', 'B) alt0a', 'C) alt0b', 'D) alt0c']
    """
    if not correct_answer:
        correct_answer = ""

    # Sanitize the correct answer (removes prefix, escapes HTML)
    sanitized = sanitize_answer(correct_answer)

    # Create placeholder options with proper formatting
    options = [
        MCQ_OPTION_FORMAT.format(letter='A', text=sanitized),
        MCQ_OPTION_FORMAT.format(letter='B', text=f'alt{attempt_num}a'),
        MCQ_OPTION_FORMAT.format(letter='C', text=f'alt{attempt_num}b'),
        MCQ_OPTION_FORMAT.format(letter='D', text=f'alt{attempt_num}c'),
    ]

    return options
