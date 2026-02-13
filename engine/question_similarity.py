"""Question similarity detection to avoid similar follow-up questions."""
import re
from difflib import SequenceMatcher
from engine.question_options import SIMILARITY_THRESHOLD


def normalize_question_text(text):
    """Normalize question text for comparison.

    Removes numbers and single-letter variable names, but keeps content words
    that differentiate questions (like "items", "stars", "candies").
    Example: "What is 5 + 3?" → "what is ? + ?"
    Example: "If you have 3 groups with 5 items..." → "if you have ? groups with ? items"
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace numbers (0-9, decimals, fractions) with placeholder
    text = re.sub(r'\d+\.?\d*', '?', text)

    # Remove only single-letter variable names (standalone a-z)
    # Keep multi-letter words that differentiate questions
    text = re.sub(r'\b[a-z]\b', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def text_similarity(text1, text2):
    """Calculate text similarity score between 0 and 1.

    Uses SequenceMatcher ratio for similarity comparison.
    """
    if not text1 or not text2:
        return 0.0

    norm1 = normalize_question_text(text1)
    norm2 = normalize_question_text(text2)

    if not norm1 or not norm2:
        return 0.0

    return SequenceMatcher(None, norm1, norm2).ratio()


def is_similar_to_any(question_text, exclude_questions, threshold=SIMILARITY_THRESHOLD):
    """Check if question is similar to any excluded question.

    Args:
        question_text: The new question text to check
        exclude_questions: List of question texts to compare against
        threshold: Similarity threshold (0-1). Default 0.7 means 70% similar.

    Returns:
        (is_similar: bool, most_similar: str or None, similarity_score: float)
    """
    if not exclude_questions:
        return False, None, 0.0

    max_similarity = 0.0
    most_similar_question = None

    for excluded_text in exclude_questions:
        similarity = text_similarity(question_text, excluded_text)
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_question = excluded_text

    is_similar = max_similarity >= threshold
    return is_similar, most_similar_question, max_similarity
