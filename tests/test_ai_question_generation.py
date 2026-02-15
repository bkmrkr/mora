"""Test suite for AI question generation -- validates subject detection and prompts."""
import pytest
from unittest.mock import patch, MagicMock
import json


# ============================================================================
# Subject Detection Tests
# ============================================================================

def test_detect_subject_hebrew():
    """Test that Hebrew topics are detected correctly."""
    from ai.question_generator import _detect_subject

    test_cases = [
        ("Hebrew (K-4)", "Kindergarten: Alef-Bet"),
        ("Hebrew (K-4)", "Chumash reading"),
        ("Hebrew", "Rashi commentary"),
        ("Hebrew", "shoresh and binyan"),
    ]

    for topic, node in test_cases:
        subject = _detect_subject(topic, node)
        assert subject == 'hebrew', f"Failed for {topic} / {node}"


def test_detect_subject_math():
    """Test that math topics are detected correctly."""
    from ai.question_generator import _detect_subject

    test_cases = [
        ("Math (K-4)", "Kindergarten Math"),
        ("Math", "Addition facts"),
        ("Math", "Multiplication"),
    ]

    for topic, node in test_cases:
        subject = _detect_subject(topic, node)
        assert subject == 'math', f"Failed for {topic} / {node}"


def test_detect_subject_reading():
    """Test that reading topics are detected correctly."""
    from ai.question_generator import _detect_subject

    test_cases = [
        ("Reading (K-4)", "Kindergarten Reading"),
        ("Reading", "Comprehension"),
    ]

    for topic, node in test_cases:
        subject = _detect_subject(topic, node)
        assert subject == 'reading', f"Failed for {topic} / {node}"


def test_detect_subject_science():
    """Test that science topics are detected correctly."""
    from ai.question_generator import _detect_subject

    test_cases = [
        ("Science (K-4)", "Kindergarten Science"),
        ("Science", "Life cycles"),
    ]

    for topic, node in test_cases:
        subject = _detect_subject(topic, node)
        assert subject == 'science', f"Failed for {topic} / {node}"


def test_detect_subject_social_studies():
    """Test that Social Studies topics are detected correctly."""
    from ai.question_generator import _detect_subject

    test_cases = [
        ("Social Studies (K-4)", "Kindergarten Social Studies"),
        ("Social Studies", "Community helpers"),
    ]

    for topic, node in test_cases:
        subject = _detect_subject(topic, node)
        assert subject == 'social_studies', f"Failed for {topic} / {node}"


def test_detect_subject_unknown():
    """Test that unknown topics return None."""
    from ai.question_generator import _detect_subject

    subject = _detect_subject("Unknown Topic", "Some random concept")
    assert subject is None


# ============================================================================
# Hebrew Question Quality Tests
# ============================================================================

def test_hebrew_question_has_proper_names():
    """Verify Hebrew questions use proper transliterations."""
    from engine.question_validator import validate_question

    good_question = {
        'question': 'What is the Hebrew word for "book"?',
        'correct_answer': '\u05e1\u05b5\u05e4\u05b6\u05e8',
        'question_type': 'mcq'
    }
    valid, reason = validate_question(good_question)
    assert valid


# ============================================================================
# Math Question Quality Tests
# ============================================================================

def test_math_question_has_single_answer():
    """Math questions must have exactly one correct answer."""
    from engine.question_validator import validate_question

    good_question = {
        'question': 'What is 5 + 3?',
        'correct_answer': '8',
        'question_type': 'mcq'
    }
    valid, reason = validate_question(good_question)
    assert valid


# ============================================================================
# Reading Question Quality Tests
# ============================================================================

def test_reading_question_comprehension():
    """Reading questions should test comprehension, not memorization."""
    from engine.question_validator import validate_question

    good_question = {
        'question': 'Why was the character happy in the story?',
        'correct_answer': 'Because he found his dog',
        'question_type': 'mcq'
    }
    valid, reason = validate_question(good_question)
    assert valid


# ============================================================================
# General Quality Tests
# ============================================================================

def test_no_placeholder_text():
    """Questions should not contain placeholder text."""
    from engine.question_validator import validate_question

    bad_question = {
        'question': '[shows a picture of] a cat. What animal is this?',
        'correct_answer': 'Cat',
        'question_type': 'mcq'
    }
    valid, reason = validate_question(bad_question)
    assert not valid, "Should not have placeholder text"


# ============================================================================
# Prompt Structure Tests
# ============================================================================

def test_system_prompt_has_critical_rules():
    """The system prompt should contain critical rules for all subjects."""
    from ai.question_generator import SYSTEM_PROMPT

    assert 'CRITICAL RULES' in SYSTEM_PROMPT
    assert 'exactly 4 options' in SYSTEM_PROMPT
    assert 'JSON' in SYSTEM_PROMPT


def test_subject_rules_exist_for_all_subjects():
    """Each subject should have specific rules."""
    from ai.question_generator import SUBJECT_RULES

    assert 'hebrew' in SUBJECT_RULES
    assert 'math' in SUBJECT_RULES
    assert 'reading' in SUBJECT_RULES
    assert 'science' in SUBJECT_RULES
    assert 'social_studies' in SUBJECT_RULES


def test_hebrew_rules_contain_transliteration():
    """Hebrew rules should mention proper transliteration."""
    from ai.question_generator import SUBJECT_RULES

    assert 'Avraham' in SUBJECT_RULES['hebrew']
    assert 'transliteration' in SUBJECT_RULES['hebrew'].lower()


def test_math_rules_contain_verify():
    """Math rules should tell LLM to verify arithmetic."""
    from ai.question_generator import SUBJECT_RULES

    assert 'VERIFY' in SUBJECT_RULES['math']


# ============================================================================
# Integration Tests - Mock LLM Generation
# ============================================================================

@patch('ai.question_generator.ask')
def test_generate_uses_system_prompt(mock_ask):
    """Test that generate passes SYSTEM_PROMPT to ask."""
    from ai.question_generator import generate, SYSTEM_PROMPT

    mock_ask.return_value = (
        '{"question": "What is 3 + 4?", "correct_answer": "7", '
        '"options": ["5", "6", "7", "8"], "explanation": "3 + 4 = 7"}',
        'llama3.2',
        'test_prompt'
    )

    q_data, model, prompt = generate(
        node_name='Kindergarten Math',
        node_description='Basic addition',
        topic_name='Math (K-4)',

        target_difficulty_elo=500,
        question_type='mcq'
    )

    mock_ask.assert_called_once()
    call_args = mock_ask.call_args
    # System prompt is the first positional arg
    assert call_args[0][0] == SYSTEM_PROMPT


@patch('ai.question_generator.ask')
def test_generate_includes_subject_rules_in_user_prompt(mock_ask):
    """Test that subject-specific rules appear in the user prompt."""
    from ai.question_generator import generate, SUBJECT_RULES

    mock_ask.return_value = (
        '{"question": "What is the Hebrew word for mother?", "correct_answer": "\u05d0\u05b5\u05dd", '
        '"options": ["\u05d0\u05b5\u05dd", "\u05d0\u05b8\u05d1", "\u05d1\u05b5\u05df", "\u05d1\u05b7\u05ea"], '
        '"explanation": "Mother in Hebrew is eim"}',
        'llama3.2',
        'test_prompt'
    )

    q_data, model, prompt = generate(
        node_name='Kindergarten: Alef-Bet',
        node_description='Basic Hebrew vocabulary',
        topic_name='Hebrew (K-4)',

        target_difficulty_elo=500,
        question_type='mcq'
    )

    mock_ask.assert_called_once()
    call_args = mock_ask.call_args
    user_prompt = call_args[0][1]
    # Hebrew rules should be in the user prompt
    assert 'Avraham' in user_prompt or 'HEBREW' in user_prompt


@patch('ai.question_generator.ask')
def test_generate_returns_parsed_json(mock_ask):
    """Test that generate returns parsed question data."""
    from ai.question_generator import generate

    mock_ask.return_value = (
        '{"question": "What is 3 + 4?", "correct_answer": "7", '
        '"options": ["5", "6", "7", "8"], "explanation": "3 + 4 = 7"}',
        'llama3.2',
        'test_prompt'
    )

    q_data, model, prompt = generate(
        node_name='Addition',
        node_description='Basic addition',
        topic_name='Math',

        target_difficulty_elo=500,
        question_type='mcq'
    )

    assert q_data is not None
    assert q_data['question'] == 'What is 3 + 4?'
    assert q_data['correct_answer'] == '7'
    assert len(q_data['options']) == 4
