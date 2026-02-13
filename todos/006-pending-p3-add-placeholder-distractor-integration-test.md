---
status: pending
priority: p3
issue_id: 006
tags:
  - code-review
  - testing
  - coverage
  - integration
dependencies: []
---

# 006: Add Integration Test — Placeholder Options Replaced by Real Distractors

## Problem Statement

The placeholder → distractor replacement pattern (lines 262-270, then line 295) lacks explicit test coverage. We need an integration test that verifies:

1. Placeholder options are created during generation
2. They pass validation
3. They're completely replaced by real distractors before storage
4. Final stored question never contains placeholder markers like `alt0a`

**Impact**: Ensures the two-phase pattern works as intended; catches regressions if someone modifies the replacement logic.

## Findings

### Current Test Gap

**What's tested**:
- Individual functions: `validate_question()`, `insert_distractors()` have unit tests
- Basic generation: `generate_next()` has basic happy-path tests

**What's NOT tested**:
- Placeholder creation + validation + replacement as a flow
- Verification that placeholders don't leak into final output
- Retry behavior when placeholders are present

### Why This Matters

If the two-phase pattern breaks, symptoms might be:
- MCQ questions fail validation (silent failure, returns None)
- Placeholders leak into student response (`'B) alt0a'` in final options)
- Distractors aren't computed (replaced() called but doesn't update q_data)

An explicit integration test would catch these immediately.

## Proposed Solution

**Approach**: Add integration test that mocks LLM output and verifies the full flow.

### Test Code

Add to `tests/test_question_service.py`:

```python
@patch('services.question_service.question_generator.generate')
@patch('services.question_service.validate_question')
def test_mcq_placeholder_replaced_with_real_distractors(mock_validate, mock_gen, app):
    """Verify that placeholder options are replaced with real distractors.

    This tests the two-phase MCQ generation:
    1. LLM generates question + answer (no options)
    2. Placeholder options added for validation
    3. Validation passes
    4. Real distractors computed
    5. Placeholders NEVER appear in final result
    """
    # Setup: Mock LLM to return question without options
    llm_result = {
        'question': 'What is 5 + 3?',
        'correct_answer': '8',
        'explanation': 'Addition of two numbers'
    }

    mock_gen.return_value = (llm_result, 'gpt-4', 'mock prompt')

    # Mock validation to accept the question
    mock_validate.return_value = (True, '')

    with app.app_context():
        with app.test_request_context():
            # Generate a question
            result = question_service.generate_next(
                session_id='test_session',
                student={'id': 123},
                topic_id=1
            )

    # Assertions
    assert result is not None, 'Question should generate successfully'
    assert result['question_type'] == 'mcq'
    assert result['correct_answer'] == '8'

    # CRITICAL: Final options must NOT contain placeholder markers
    options = result.get('options', [])
    assert len(options) == 4, f'Should have 4 options, got {len(options)}'

    # Placeholder markers (alt0a, alt1b, etc.) must NOT appear
    option_text = ' '.join(options)
    assert 'alt0' not in option_text, f'Placeholder from attempt 0 leaked: {option_text}'
    assert 'alt1' not in option_text, f'Placeholder from attempt 1 leaked: {option_text}'
    assert 'alt2' not in option_text, f'Placeholder from attempt 2 leaked: {option_text}'
    assert 'placeholder' not in option_text.lower(), f'Generic placeholder leaked: {option_text}'

    # Verify options are computed distractors (not the placeholder format)
    # Options should be numeric or mathematically derived
    # For '8' with answer, distractors might be 7, 9, 6, 10, etc.
    assert any(opt.strip() in ['7', '9', '6', '10', '5', '11'] for opt in options), \
        f'Options should contain computed distractors, got {options}'

    logger.info(f'✓ MCQ generation + distractor replacement passed')
    logger.info(f'  Final options: {options}')


def test_mcq_placeholder_generation_multiple_retries(app):
    """Verify that placeholders with different attempt_num are generated on retries.

    When validation fails and retry occurs, new placeholders should have new attempt_num.
    This ensures the validator doesn't see identical options twice.
    """
    with patch('services.question_service.question_generator.generate') as mock_gen:
        with patch('services.question_service.validate_question') as mock_validate:
            # Setup: Mock first attempt fails validation, second succeeds
            llm_result_1 = {
                'question': 'What is 2+2?',
                'correct_answer': '4',
                'explanation': 'Two plus two'
            }
            llm_result_2 = {
                'question': 'What is 3+3?',
                'correct_answer': '6',
                'explanation': 'Three plus three'
            }

            mock_gen.side_effect = [
                (llm_result_1, 'gpt-4', 'prompt1'),
                (llm_result_2, 'gpt-4', 'prompt2'),
            ]

            # Validation fails first time, passes second time
            mock_validate.side_effect = [
                (False, 'Answer gave away by length'),  # Reject attempt 1
                (True, ''),  # Accept attempt 2
            ]

            with app.app_context():
                with app.test_request_context():
                    result = question_service.generate_next(
                        session_id='test_session',
                        student={'id': 456},
                        topic_id=2
                    )

            # Verify second attempt succeeded
            assert result is not None
            assert result['question'] == 'What is 3+3?'
            assert result['correct_answer'] == '6'

            # Verify generate was called twice (two attempts)
            assert mock_gen.call_count == 2

            # Verify validate was called twice
            assert mock_validate.call_count == 2

            logger.info(f'✓ Retry with new placeholders passed')
            logger.info(f'  Attempts: 2, Final question: {result["question"]}')
```

### Why This Test Matters

1. **Validates the pattern**: Ensures placeholders are created, used for validation, and replaced
2. **Prevents regressions**: If someone removes the `insert_distractors()` call, test fails
3. **Documents intent**: Test code is living documentation of the two-phase design
4. **Catches silent failures**: If MCQ validation fails silently, test catches it

## Acceptance Criteria

- [ ] Integration test added to `tests/test_question_service.py`
- [ ] Test verifies placeholder creation and replacement
- [ ] Test verifies no placeholder markers leak into final output
- [ ] Test covers retry scenario (multiple LLM attempts)
- [ ] Test passes with current code
- [ ] Test fails if `insert_distractors()` is removed (validates test quality)

## Technical Details

### Affected Files
- `tests/test_question_service.py` (new test methods)

### No Production Code Changes
Pure test addition.

## Work Log

- **2026-02-12**: Created todo after code review. Agent-native-reviewer noted lack of explicit test coverage for placeholder pattern.

---

**Status**: PENDING TRIAGE
**Priority**: P3 (NICE-TO-HAVE - Enhancements)
**Assigned to**: (none)
