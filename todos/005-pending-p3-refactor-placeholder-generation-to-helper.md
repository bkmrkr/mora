---
status: pending
priority: p3
issue_id: 005
tags:
  - code-review
  - quality
  - refactoring
  - testability
dependencies: []
---

# 005: Refactor Placeholder Generation to Helper Function

## Problem Statement

The placeholder MCQ options generation code (lines 262-270) is embedded directly in the retry loop. Extracting it to a dedicated helper function would improve testability, reusability, and code clarity.

**Impact**: Easier to test placeholder generation independently, clearer intent, easier to modify if needed.

## Findings

### Current Inline Code
```python
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = [
        f'A) {correct}',
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]
```

**Issues**:
- Hard to test in isolation
- Can only test via full `generate_next()` mocking
- Business logic (how to generate placeholders) is mixed with orchestration (retry loop)
- If placeholder format changes, must modify generate_next()

### Testing Impact

Currently, to test placeholder generation, you must:
```python
@patch('question_generator.generate')
@patch('validate_question')
def test_mcq_placeholder_generation(mock_val, mock_gen):
    # Mock the entire generation pipeline
    # Call generate_next()
    # Verify placeholder structure by reading logs or inspecting DB
    # All mocking overhead for a 9-line function!
```

With a helper function, you can directly test:
```python
def test_create_placeholder_options():
    options = create_placeholder_options('12', attempt_num=0)
    assert options == ['A) 12', 'B) alt0a', 'C) alt0b', 'D) alt0c']
    assert len(options) == 4
    assert all('alt' in opt for opt in options[1:])
```

## Proposed Solutions

### Solution A: Helper Function in Same File (RECOMMENDED)
**Approach**: Define a private helper function in `services/question_service.py`

**Code**:
```python
def _create_placeholder_options(correct_answer: str, attempt_num: int) -> list[str]:
    """Create temporary MCQ placeholder options for validation.

    The validator requires options to check structural rules (uniqueness, min count).
    These placeholders serve only to satisfy validation; they're replaced by
    computed distractors before storage (see insert_distractors()).

    Args:
        correct_answer: The correct answer (e.g., '12', '3/4')
        attempt_num: Which retry attempt this is (0, 1, 2)

    Returns:
        List of 4 placeholder option strings with letter prefixes.

    Example:
        >>> _create_placeholder_options('12', 0)
        ['A) 12', 'B) alt0a', 'C) alt0b', 'D) alt0c']
    """
    return [
        f'A) {correct_answer}',
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]

# Usage in generate_next() at line 262:
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = _create_placeholder_options(correct, attempt_num)
```

**Pros**:
- Testable in isolation
- Clear intent with docstring
- Private function (underscore prefix) indicates internal use
- Easier to modify placeholder format
- No new file/import overhead

**Cons**:
- Adds 15 lines of code (function def + docstring)
- Minimal in terms of actual logic extraction

**Effort**: Small (extract 9 lines into function with docstring)
**Risk**: Very low (refactoring only)

### Solution B: Helper Function in ai/distractors.py
**Approach**: Move placeholder generation to the distractor module where it logically belongs.

**Rationale**: All MCQ option handling (placeholders + real distractors) in one place.

**Code**:
```python
# In ai/distractors.py (new function)

def create_placeholder_options(correct_answer: str, attempt_num: int) -> list[str]:
    """Create temporary MCQ options for validation.

    See generate_next() in services/question_service.py for context.
    """
    return [
        f'A) {correct_answer}',
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]

# Usage in services/question_service.py:
from ai.distractors import create_placeholder_options

if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = create_placeholder_options(correct, attempt_num)
```

**Pros**:
- Logically grouped with `insert_distractors()`
- All MCQ option logic in one module
- Cleaner separation of concerns

**Cons**:
- Adds new public function to `ai.distractors` module
- New import in services
- Slightly more indirection

**Effort**: Small (function + import)
**Risk**: Low (new function, no breaking changes)

### Solution C: Extract to Separate Utility Module
**Approach**: Create new `ai/placeholder_generation.py` module.

**Cons**:
- Overkill for a 9-line function
- Adds another file to codebase
- Over-engineering

**Verdict**: Not recommended.

## Recommended Action

Implement **Solution A** — helper function in same file.

### Step 1: Define Function
Add at the beginning of `services/question_service.py` (after imports, before `pop_cached()`):
```python
def _create_placeholder_options(correct_answer: str, attempt_num: int) -> list[str]:
    """Create temporary MCQ placeholder options for validation.

    The validator requires options to check structural rules (uniqueness, min count).
    These placeholders serve only to satisfy validation; they're replaced by
    computed distractors before storage (see insert_distractors()).

    Args:
        correct_answer: The correct answer (e.g., '12', '3/4')
        attempt_num: Which retry attempt this is (0-indexed)

    Returns:
        List of 4 placeholder option strings with letter prefixes.

    Example:
        >>> _create_placeholder_options('12', 0)
        ['A) 12', 'B) alt0a', 'C) alt0b', 'D) alt0c']
    """
    return [
        f'A) {correct_answer}',
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]
```

### Step 2: Update generate_next()
Replace lines 262-270 with:
```python
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = _create_placeholder_options(correct, attempt_num)
```

### Step 3: Add Unit Test
In `tests/test_question_service.py`, add:
```python
def test_create_placeholder_options():
    """Verify placeholder options have correct structure."""
    from services.question_service import _create_placeholder_options

    options = _create_placeholder_options('12', attempt_num=0)

    assert len(options) == 4
    assert options[0] == 'A) 12'
    assert options[1] == 'B) alt0a'
    assert options[2] == 'C) alt0b'
    assert options[3] == 'D) alt0c'

    # Verify attempt number appears in options
    options_attempt2 = _create_placeholder_options('7', attempt_num=2)
    assert options_attempt2[1] == 'B) alt2a'
    assert options_attempt2[2] == 'C) alt2b'
    assert options_attempt2[3] == 'D) alt2c'

    # Verify special characters are preserved
    options_special = _create_placeholder_options('2/3', attempt_num=0)
    assert options_special[0] == 'A) 2/3'
```

### Step 4: Verify
```bash
python3 -m pytest tests/test_question_service.py::test_create_placeholder_options -v
python3 -m pytest tests/test_question_service.py -v  # Full suite
```

## Acceptance Criteria

- [ ] `_create_placeholder_options()` function defined with docstring
- [ ] Function is testable in isolation
- [ ] Unit test added and passing
- [ ] `generate_next()` updated to use new function
- [ ] No changes to behavior or output
- [ ] All existing tests still pass

## Technical Details

### Affected Files
- `services/question_service.py` (new function + updated generate_next)
- `tests/test_question_service.py` (new test)

### No Database or API Changes
Purely refactoring for maintainability.

## Work Log

- **2026-02-12**: Created todo after code review. Architecture-strategist and pattern-recognition-specialist recommended extracting for clarity and testability.

## Resources

- Single Responsibility Principle
- Function extraction as code smell removal

---

**Status**: PENDING TRIAGE
**Priority**: P3 (NICE-TO-HAVE - Enhancements)
**Assigned to**: (none)
