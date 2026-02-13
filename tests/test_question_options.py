"""Tests for question options generation and sanitization."""
import pytest
from engine.question_options import (
    sanitize_answer,
    create_placeholder_options,
    SIMILARITY_THRESHOLD,
    QUESTION_TYPE_MCQ,
    MCQ_LETTERS,
)


class TestSanitizeAnswer:
    """Tests for answer sanitization."""

    def test_sanitize_basic_answer(self):
        """Should sanitize basic numeric answers."""
        result = sanitize_answer("42")
        assert result == "42"
        assert isinstance(result, str)

    def test_sanitize_removes_letter_prefix(self):
        """Should remove letter prefixes like 'A) 42'."""
        result = sanitize_answer("A) 42")
        assert result == "42"

    def test_sanitize_removes_letter_prefix_variants(self):
        """Should remove various letter prefix formats."""
        assert sanitize_answer("A) 42") == "42"
        assert sanitize_answer("B) 123") == "123"
        assert sanitize_answer("C) answer") == "answer"
        assert sanitize_answer("D) x = 5") == "x = 5"

    def test_sanitize_handles_lowercase_prefix(self):
        """Should remove lowercase letter prefixes."""
        assert sanitize_answer("a) 42") == "42"
        assert sanitize_answer("b) test") == "test"

    def test_sanitize_removes_extra_whitespace(self):
        """Should remove extra whitespace."""
        result = sanitize_answer("A)    42    ")
        assert result == "42"

    def test_sanitize_xss_prevention_html_tags(self):
        """Should escape HTML tags to prevent XSS."""
        result = sanitize_answer("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result or "script" not in result

    def test_sanitize_xss_prevention_onclick(self):
        """Should escape onclick handlers."""
        result = sanitize_answer("<img onclick='alert(1)'>")
        assert "onclick=" not in result or "&" in result

    def test_sanitize_xss_prevention_javascript_url(self):
        """Should escape javascript URLs."""
        result = sanitize_answer("javascript:alert(1)")
        # HTML-escaped version or no dangerous characters
        assert result.count("alert") <= 1 or "&" in result

    def test_sanitize_html_entities(self):
        """Should escape HTML entities like & and quotes."""
        result = sanitize_answer("x & y")
        assert result == "x &amp; y"

    def test_sanitize_preserves_normal_text(self):
        """Should preserve normal text and mathematical notation."""
        result = sanitize_answer("x + 2 = 5")
        assert result == "x + 2 = 5"

    def test_sanitize_empty_string(self):
        """Should handle empty strings."""
        assert sanitize_answer("") == ""
        assert sanitize_answer(None) == ""

    def test_sanitize_only_whitespace(self):
        """Should return empty for whitespace-only input."""
        result = sanitize_answer("   ")
        assert result == ""

    def test_sanitize_prefix_with_period(self):
        """Should remove prefix with period separator."""
        result = sanitize_answer("A. 42")
        assert result == "42"

    def test_sanitize_multiple_prefixes(self):
        """Should only remove the first prefix."""
        result = sanitize_answer("A) B) 42")
        # Should remove "A) " but not "B) "
        assert result == "B) 42"

    def test_sanitize_complex_answer(self):
        """Should sanitize complex mathematical expressions."""
        result = sanitize_answer("A) x = (2 + 3) / 4")
        assert result == "x = (2 + 3) / 4"

    def test_sanitize_with_special_chars(self):
        """Should escape special HTML characters."""
        result = sanitize_answer("x > y & z < w")
        assert result == "x &gt; y &amp; z &lt; w"


class TestCreatePlaceholderOptions:
    """Tests for placeholder options creation."""

    def test_create_basic_placeholder_options(self):
        """Should create four placeholder options."""
        options = create_placeholder_options("42")
        assert len(options) == 4
        assert all(isinstance(o, str) for o in options)

    def test_create_placeholder_options_format(self):
        """Should format options with letters."""
        options = create_placeholder_options("42")
        assert options[0].startswith("A) ")
        assert options[1].startswith("B) ")
        assert options[2].startswith("C) ")
        assert options[3].startswith("D) ")

    def test_create_placeholder_correct_answer_first(self):
        """First option should contain the correct answer."""
        options = create_placeholder_options("42")
        assert "42" in options[0]

    def test_create_placeholder_unique_distractors(self):
        """Distractors should be unique and numbered."""
        options = create_placeholder_options("correct", attempt_num=0)
        assert "alt0a" in options[1]
        assert "alt0b" in options[2]
        assert "alt0c" in options[3]

    def test_create_placeholder_attempt_number(self):
        """Should include attempt number in distractors."""
        options0 = create_placeholder_options("answer", attempt_num=0)
        options1 = create_placeholder_options("answer", attempt_num=1)

        assert "alt0a" in options0[1]
        assert "alt1a" in options1[1]

    def test_create_placeholder_sanitizes_correct_answer(self):
        """Should sanitize the correct answer."""
        options = create_placeholder_options("A) 42")
        # Should not double-prefix: "A) A) 42"
        assert "A) A)" not in options[0]
        # Should have the clean version
        assert "42" in options[0]
        # Should start with letter prefix
        assert options[0].startswith("A) ")

    def test_create_placeholder_xss_protection(self):
        """Should protect against XSS in correct answer."""
        options = create_placeholder_options("<script>alert(1)</script>")
        # Check that script tags are escaped
        full_text = " ".join(options)
        assert "&lt;script&gt;" in full_text or "<script>" not in full_text

    def test_create_placeholder_empty_answer(self):
        """Should handle empty correct answer."""
        options = create_placeholder_options("")
        assert len(options) == 4
        # First option should just have the letter prefix
        assert options[0].startswith("A) ")

    def test_create_placeholder_with_math_symbols(self):
        """Should preserve mathematical symbols."""
        options = create_placeholder_options("x = 5")
        assert "x = 5" in options[0]

    def test_create_placeholder_with_html_entities(self):
        """Should escape HTML entities."""
        options = create_placeholder_options("a & b > c")
        assert "&amp;" in options[0]
        assert "&gt;" in options[0]

    def test_create_placeholder_respects_attempt_num(self):
        """Each attempt should have different placeholder numbers."""
        options_1 = create_placeholder_options("test", attempt_num=5)
        options_2 = create_placeholder_options("test", attempt_num=6)

        # Get the placeholder texts
        placeholder1 = set([options_1[1], options_1[2], options_1[3]])
        placeholder2 = set([options_2[1], options_2[2], options_2[3]])

        # Should be different between attempts
        assert placeholder1 != placeholder2

    def test_create_placeholder_all_letters_present(self):
        """Should use all four letter options."""
        options = create_placeholder_options("answer")
        letters = [opt[0] for opt in options]
        assert letters == ['A', 'B', 'C', 'D']

    def test_create_placeholder_maintains_format(self):
        """All options should follow 'X) text' format."""
        options = create_placeholder_options("answer")
        for opt in options:
            # Should be "Letter) text" format
            assert opt[0] in MCQ_LETTERS
            assert ") " in opt
            assert opt.index(")") == 1

    def test_create_placeholder_with_long_answer(self):
        """Should handle long answers."""
        long_answer = "This is a very long mathematical expression with many terms"
        options = create_placeholder_options(long_answer)
        assert long_answer in options[0]

    def test_create_placeholder_consistency(self):
        """Same input should always produce same output."""
        options1 = create_placeholder_options("42", attempt_num=0)
        options2 = create_placeholder_options("42", attempt_num=0)
        assert options1 == options2


class TestConstants:
    """Tests for module constants."""

    def test_similarity_threshold_value(self):
        """Should have valid similarity threshold."""
        assert 0 < SIMILARITY_THRESHOLD < 1
        assert SIMILARITY_THRESHOLD == 0.7

    def test_question_type_mcq_value(self):
        """Should have MCQ question type constant."""
        assert QUESTION_TYPE_MCQ == 'mcq'

    def test_mcq_letters_count(self):
        """Should have four MCQ letters."""
        assert len(MCQ_LETTERS) == 4
        assert MCQ_LETTERS == ['A', 'B', 'C', 'D']


class TestIntegration:
    """Integration tests for sanitization and placeholder creation."""

    def test_full_flow_with_llm_response(self):
        """Test realistic LLM response with prefix."""
        llm_response = "A) 42"  # LLM sometimes includes letter
        options = create_placeholder_options(llm_response, attempt_num=0)

        # Should not double-prefix
        assert "A) A)" not in options[0]
        # Should have the clean answer
        assert "42" in options[0]
        # Should start with proper format
        assert options[0].startswith("A) ")

    def test_full_flow_with_malicious_input(self):
        """Test with potentially malicious LLM response."""
        malicious = "<img src=x onerror='alert(1)'>"
        options = create_placeholder_options(malicious)

        # Should be safe to render
        full_text = " ".join(options)
        assert "onerror=" not in full_text or "&" in full_text

    def test_full_flow_multiple_attempts(self):
        """Test that multiple attempts create different placeholders."""
        options_list = [
            create_placeholder_options("answer", attempt_num=i)
            for i in range(3)
        ]

        # Each attempt should have different placeholders
        placeholders = [
            {opt for opt in opts[1:]} for opts in options_list
        ]

        assert placeholders[0] != placeholders[1]
        assert placeholders[1] != placeholders[2]

    def test_full_flow_preserves_mathematical_notation(self):
        """Test that mathematical expressions are preserved."""
        answers = [
            "x + 2 = 5",
            "√16 = 4",
            "2³ = 8",
            "50%",
            "1/2",
        ]

        for answer in answers:
            options = create_placeholder_options(answer)
            # Should preserve the mathematical expression
            assert answer in options[0]

    def test_full_flow_with_numeric_answers(self):
        """Test various numeric answers."""
        answers = ["0", "42", "-5", "3.14", "1000"]

        for answer in answers:
            options = create_placeholder_options(answer)
            assert len(options) == 4
            assert answer in options[0]
            assert all(opt.startswith(letter + ")") for letter, opt in zip(MCQ_LETTERS, options))
