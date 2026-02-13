"""Tests for question similarity detection."""
import pytest
from engine.question_similarity import normalize_question_text, text_similarity, is_similar_to_any


class TestNormalizeQuestionText:
    """Tests for text normalization."""

    def test_normalize_removes_numbers(self):
        """Should replace all numbers with ?"""
        result = normalize_question_text("What is 5 + 3?")
        assert "5" not in result
        assert "3" not in result
        assert "?" in result

    def test_normalize_removes_variables(self):
        """Should remove variable names."""
        result = normalize_question_text("Solve for x: x + 5 = 10")
        assert "x" not in result.lower() or "x" in "?+ ? = ?"  # x might be removed or become ?

    def test_normalize_case_insensitive(self):
        """Should convert to lowercase."""
        result1 = normalize_question_text("What is 5 + 3?")
        result2 = normalize_question_text("WHAT IS 5 + 3?")
        assert result1 == result2

    def test_normalize_whitespace(self):
        """Should normalize multiple spaces."""
        result = normalize_question_text("What    is    5    +    3?")
        assert "  " not in result  # No double spaces

    def test_normalize_similar_arithmetic_questions(self):
        """Similar arithmetic questions should normalize similarly."""
        q1 = normalize_question_text("What is 5 + 3?")
        q2 = normalize_question_text("What is 7 + 2?")
        # Both should have the same structure
        assert q1 == q2


class TestTextSimilarity:
    """Tests for text similarity scoring."""

    def test_identical_questions_are_100_percent_similar(self):
        """Identical questions should have ~1.0 similarity."""
        similarity = text_similarity("What is 5 + 3?", "What is 5 + 3?")
        assert similarity == 1.0

    def test_completely_different_questions_have_low_similarity(self):
        """Completely different questions should have low similarity."""
        similarity = text_similarity("What is 5 + 3?", "What is the capital of France?")
        assert similarity < 0.5

    def test_similar_arithmetic_questions(self):
        """Similar arithmetic questions should have high similarity."""
        # "What is 5 + 3?" vs "What is 7 + 2?" should both be addition
        similarity = text_similarity("What is 5 + 3?", "What is 7 + 2?")
        assert similarity > 0.7

    def test_similar_multiplication_questions(self):
        """Similar multiplication questions should have high similarity."""
        similarity = text_similarity("What is 5 × 3?", "What is 8 × 2?")
        assert similarity > 0.7

    def test_subtraction_vs_addition_have_high_similarity(self):
        """Subtraction vs addition both normalize to same structure.

        After normalization, both become "what is ? ?" so they're highly similar.
        This is intentional - we want to avoid similar arithmetic questions.
        """
        similarity = text_similarity("What is 5 + 3?", "What is 5 - 3?")
        # Both normalize to the same structure, so high similarity is expected
        assert similarity > 0.8

    def test_empty_strings_have_zero_similarity(self):
        """Empty strings should have 0 similarity."""
        assert text_similarity("", "") == 0.0
        assert text_similarity("What is 5?", "") == 0.0
        assert text_similarity("", "What is 5?") == 0.0


class TestIsSimilarToAny:
    """Tests for checking similarity against a set of questions."""

    def test_identical_question_is_similar(self):
        """Should detect identical questions as similar."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            ["What is 5 + 3?"],
            threshold=0.9
        )
        assert is_similar is True
        assert score == 1.0

    def test_below_threshold_not_similar(self):
        """Questions below threshold should not be flagged as similar."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            ["What is the capital of France?"],
            threshold=0.9
        )
        assert is_similar is False
        assert score < 0.5

    def test_above_threshold_is_similar(self):
        """Questions above threshold should be flagged as similar."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            ["What is 7 + 2?"],
            threshold=0.7
        )
        assert is_similar is True
        assert score > 0.7

    def test_returns_most_similar_question(self):
        """Should return the most similar question from the list."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            [
                "What is the capital of France?",
                "What is 7 + 2?",
                "What is 6 × 4?"
            ],
            threshold=0.6
        )
        assert similar_q == "What is 7 + 2?"

    def test_empty_exclude_list(self):
        """Empty exclude list should not be similar."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            [],
            threshold=0.7
        )
        assert is_similar is False
        assert similar_q is None
        assert score == 0.0

    def test_multiple_similar_questions(self):
        """Should find the most similar among multiple similar questions."""
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 + 3?",
            [
                "What is 7 + 2?",
                "What is 8 + 1?",
                "What is 6 + 3?"
            ],
            threshold=0.6
        )
        assert is_similar is True
        assert similar_q is not None
        # Should be one of the addition questions
        assert "+" in similar_q or "add" in similar_q.lower()


class TestAvoidingSimilarQuestions:
    """Integration tests for the main use case."""

    def test_avoid_similar_arithmetic_sequence(self):
        """Should prevent asking "5+3" followed by "7+2"."""
        correctly_answered = [
            "What is 5 + 3?",
            "What is 12 × 4?",
            "What is 20 ÷ 4?"
        ]

        # New question "7 + 2" should be flagged as similar to "5 + 3"
        is_similar, similar_q, score = is_similar_to_any(
            "What is 7 + 2?",
            correctly_answered,
            threshold=0.7
        )
        assert is_similar is True

    def test_avoid_different_operation_same_numbers(self):
        """Should avoid arithmetic questions with same numbers.

        "5 + 3" and "5 × 3" are different operations, but use same numbers.
        After normalization, both become "what is ? ?" so they're very similar.
        This is intentional to maximize question variety.
        """
        correctly_answered = ["What is 5 + 3?"]

        # Multiplication question WILL be flagged as similar due to same numbers
        is_similar, similar_q, score = is_similar_to_any(
            "What is 5 × 3?",
            correctly_answered,
            threshold=0.7
        )
        # Both normalize to the same structure, so they'll be similar
        assert is_similar is True
        assert score > 0.7

    def test_allow_different_topic(self):
        """Should allow completely different topic after correct answer."""
        correctly_answered = ["What is 5 + 3?"]

        # Word problem should not be similar
        is_similar, similar_q, score = is_similar_to_any(
            "If John has 5 apples and Mary has 3, how many do they have together?",
            correctly_answered,
            threshold=0.7
        )
        # This should be below threshold or no similarity
        assert not is_similar or score < 0.5
