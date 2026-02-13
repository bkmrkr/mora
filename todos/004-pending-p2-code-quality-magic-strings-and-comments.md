---
status: pending
priority: p2
issue_id: 004
tags:
  - code-review
  - quality
  - style
  - maintainability
dependencies: []
---

# 004: Code Quality — Magic Strings, Redundant Comments, Missing Type Hints

## Problem Statement

The `services/question_service.py` file has three code quality issues:

1. **Magic strings**: Placeholder format (`alt{attempt_num}a`) is hardcoded without constants
2. **Redundant comments**: Same concept explained 3 times across 6 lines (lines 260-261, 264-265)
3. **Missing type hints**: `generate_next()` function (line 115) has no type annotations

These issues reduce maintainability and make code harder to understand.

## Findings

### Issue 1: Magic String Constants

**Location**: Lines 265-270 in `services/question_service.py`
```python
q_data['options'] = [
    f'A) {correct}',           # ✓ Clear intent
    f'B) alt{attempt_num}a',   # ✗ Magic string: what is "alt"? Why "a"?
    f'C) alt{attempt_num}b',   # ✗ Magic string
    f'D) alt{attempt_num}c'    # ✗ Magic string
]
```

**Problems**:
- `alt{attempt_num}a` is unexplained — no constant definition
- If this format appears elsewhere, no single source of truth
- Hard to grep/search for all uses
- Makes code harder to change (e.g., if you want to rename `alt` to `placeholder`)

**Also in letter prefixes**:
- Hardcoded `A)`, `B)`, `C)`, `D)` (lines 266-269)
- Similar hardcoding in `ai/distractors.py:209` (`letters[correct_index]`)
- No shared constant for `OPTION_LETTERS`

### Issue 2: Redundant Comments

**Location**: Lines 260-265 in `services/question_service.py`
```python
# Validate the generated question
# For MCQ, add placeholder options for validation (will be replaced with computed distractors)
# Use attempt number to make placeholders unique across retries
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    # Use attempt_num to make options unique across retries
```

**Issues**:
- Line 261: "add placeholder options for validation"
- Line 262: "will be replaced with computed distractors" ← first mention
- Line 263: "Use attempt number to make placeholders unique"
- Line 265 (inside if): "Use attempt_num to make options unique across retries" ← REPEATED

**Result**: 3 comment lines before code, 1 inside code, all explaining the same thing.

**Better approach**: One clear comment explaining all intent.

### Issue 3: Missing Type Hints

**Location**: Lines 115-132 in `services/question_service.py`
```python
def generate_next(session_id, student, topic_id, store_in_session=True,
                   skill_overrides=None, last_was_correct=None):
    """Select focus node, compute difficulty, generate question...
```

**Problem**:
- No parameter type annotations
- No return type annotation
- Docstring provides some info (returns "question_dict or None")
- Inconsistent with Python best practices

**Expected format**:
```python
from typing import Optional, Any

def generate_next(
    session_id: str,
    student: dict[str, Any],
    topic_id: int,
    store_in_session: bool = True,
    skill_overrides: Optional[dict[int, float]] = None,
    last_was_correct: Optional[bool] = None,
) -> Optional[dict[str, Any]]:
    """..."""
```

## Proposed Solutions

### Solution A: Extract Constants (RECOMMENDED)
**Approach**: Define constants for letter prefixes and placeholder format.

**Code**:
```python
# At the top of services/question_service.py, after imports

# MCQ option configuration
OPTION_LETTERS = ['A', 'B', 'C', 'D']
MIN_OPTION_COUNT = 3
PLACEHOLDER_FORMAT = 'placeholder_{attempt}_{letter}'  # e.g., placeholder_0_b

# Usage in placeholder generation:
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = [
        f'{OPTION_LETTERS[0]}) {correct}',
        f'{OPTION_LETTERS[1]}) {PLACEHOLDER_FORMAT.format(attempt=attempt_num, letter="b")}',
        f'{OPTION_LETTERS[2]}) {PLACEHOLDER_FORMAT.format(attempt=attempt_num, letter="c")}',
        f'{OPTION_LETTERS[3]}) {PLACEHOLDER_FORMAT.format(attempt=attempt_num, letter="d")}',
    ]
```

**Pros**:
- Single source of truth for option format
- Easy to change letter prefixes if needed
- DRY principle
- Searchable constants

**Cons**:
- Slightly more verbose than hardcoded strings
- Format string is more complex

**Effort**: Small (4 lines for constants, 4 lines for usage)
**Risk**: Low (refactoring only)

### Solution B: Consolidate Comments
**Approach**: Combine redundant comments into one clear explanation.

**Current** (6 lines):
```python
# Validate the generated question
# For MCQ, add placeholder options for validation (will be replaced with computed distractors)
# Use attempt number to make placeholders unique across retries
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    # Use attempt_num to make options unique across retries
```

**Improved** (2 lines):
```python
# MCQ validation requires options. Generate temporary placeholders
# (will be replaced with computed distractors at line 295).
# Use attempt_num to ensure uniqueness across retry iterations.
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
```

**Pros**:
- Clearer intent
- No redundancy
- Still explains why (validation bridge), what (placeholders), and how (attempt_num)

**Cons**:
- Requires careful wording

**Effort**: Small (1 line rewritten)
**Risk**: Very low (comments only)

### Solution C: Add Type Hints to generate_next()
**Approach**: Add full type annotations to the function signature.

**Code**:
```python
from typing import Optional, Any

def generate_next(
    session_id: str,
    student: dict[str, Any],
    topic_id: int,
    store_in_session: bool = True,
    skill_overrides: Optional[dict[int, float]] = None,
    last_was_correct: Optional[bool] = None,
) -> Optional[dict[str, Any]]:
    """Select focus node, compute difficulty, generate question.

    Three dedup layers (from kidtutor):
      1. Session dedup — never repeat any question within the same session
      2. Global dedup — never repeat a correctly-answered question (lifetime)
      3. Recent texts — passed to LLM to avoid similar questions

    Post-generation validation rejects bad LLM output and retries.

    When store_in_session=True, stores in flask_session['current_question'].
    When False (pre-caching), skips session writes.

    Args:
        session_id: Unique session identifier
        student: Student dict with id, skills, etc.
        topic_id: Curriculum topic to generate question from
        store_in_session: Whether to store in flask_session (default True)
        skill_overrides: Dict of {node_id: predicted_skill_rating} for dual precache
        last_was_correct: Whether student's last answer was correct (for node selection)

    Returns:
        question_dict with all fields, or None if generation failed after max retries.
    """
```

**Pros**:
- Better IDE support (autocomplete, type checking)
- Self-documenting
- Easier refactoring
- Follows Python best practices

**Cons**:
- More verbose
- Requires understanding type annotation syntax

**Effort**: Small (5 lines added)
**Risk**: Very low (additive only)

## Recommended Action

Implement **all three solutions**:

1. **Extract constants** (Solution A): Create OPTION_LETTERS, PLACEHOLDER_FORMAT
2. **Consolidate comments** (Solution B): Reduce from 6 lines to 3
3. **Add type hints** (Solution C): Annotate function signature

### Step 1: Add Constants
At the top of `services/question_service.py` (after imports):
```python
# MCQ option configuration
OPTION_LETTERS = ['A', 'B', 'C', 'D']
MIN_OPTION_COUNT = 3
```

### Step 2: Update Placeholder Generation
Replace lines 265-270 with:
```python
q_data['options'] = [
    f'{OPTION_LETTERS[0]}) {correct}',
    f'{OPTION_LETTERS[1]}) alt{attempt_num}a',
    f'{OPTION_LETTERS[2]}) alt{attempt_num}b',
    f'{OPTION_LETTERS[3]}) alt{attempt_num}c'
]
```

### Step 3: Consolidate Comments
Replace lines 260-265 with:
```python
# MCQ validation requires options. Generate temporary placeholders
# (will be replaced with computed distractors at line 295).
# Use attempt_num to ensure uniqueness across retry iterations.
```

### Step 4: Add Type Hints
Update function signature at line 115-116:
```python
def generate_next(
    session_id: str,
    student: dict[str, Any],
    topic_id: int,
    store_in_session: bool = True,
    skill_overrides: Optional[dict[int, float]] = None,
    last_was_correct: Optional[bool] = None,
) -> Optional[dict[str, Any]]:
```

And add import at top:
```python
from typing import Optional, Any
```

### Step 5: Verify
```bash
# Run type checker (if installed)
mypy services/question_service.py

# Run tests
python3 -m pytest tests/test_question_service.py -v
```

## Acceptance Criteria

- [ ] OPTION_LETTERS constant defined
- [ ] Placeholder format uses constants (not magic strings)
- [ ] Comments consolidated to single clear explanation
- [ ] Type hints added to generate_next() signature
- [ ] All tests pass
- [ ] IDE type checking works correctly

## Technical Details

### Affected Files
- `services/question_service.py` (lines 115-116, 260-270)

### Performance Impact
None (constants are zero-cost)

### Compatibility Impact
None (purely code quality)

## Work Log

- **2026-02-12**: Created todo after code review. Kieran-python-reviewer and pattern-recognition-specialist flagged magic strings, redundant comments, and missing type hints.

## Resources

- PEP 257: Docstring Conventions
- PEP 484: Type Hints
- Python typing module: https://docs.python.org/3/library/typing.html

---

**Status**: PENDING TRIAGE
**Priority**: P2 (IMPORTANT - Should Fix)
**Assigned to**: (none)
