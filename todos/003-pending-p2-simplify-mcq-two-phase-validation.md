---
status: pending
priority: p2
issue_id: 003
tags:
  - code-review
  - architecture
  - simplification
  - design-pattern
dependencies:
  - 001
---

# 003: Simplify MCQ Validation — Two-Phase Pattern Is Unnecessary

## Problem Statement

The code implements a two-phase MCQ option generation pattern:
1. **Phase 1** (lines 262-270): Generate temporary placeholder options for validation
2. **Phase 2** (line 295): Replace placeholders with computed distractors

This pattern adds unnecessary complexity. The question validation could skip the full validation pipeline for MCQ when options aren't available yet, and simply validate core fields (question and answer exist). Then generate real distractors immediately after validation passes.

**Impact**:
- Adds 9 lines of code that do temporary work
- Creates implicit data contract: "options may be fake, replaced at line 295"
- Complicates testing and maintenance
- Attempt_num uniqueness in placeholders (lines 267-269) serves no functional purpose

## Findings

### Current Two-Phase Design

**Phase 1: Placeholder Generation**
```python
# Lines 262-270
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = [
        f'A) {correct}',
        f'B) alt{attempt_num}a',  # Attempt number for uniqueness
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]

# Then validate with placeholders
is_valid, reason = validate_question(q_data, node_desc)  # Line 272
```

**Phase 2: Distractor Replacement**
```python
# Line 295
if q_type == 'mcq' and q_data:
    q_data = insert_distractors(q_data)  # Replaces options entirely
```

**Intermediate State Problem**:
- Between line 270 and 295, `q_data['options']` contains fake data
- Validation passes on fake options (they satisfy Rules 3, 4, 9, 10)
- Real options are inserted 20+ lines later
- Implicit assumption: nothing between validation and distractor insertion uses options

### Why Placeholders Exist

The validator (question_validator.py) requires options field to validate:
- **Rule 3**: Options must be unique (prevents duplicates)
- **Rule 4**: Correct answer must be in choices
- **Rule 9**: Minimum 3 choices
- **Rule 10**: Answer length doesn't give away response

**Question**: Could MCQ validation skip these rules and validate only core structure?

**Answer**: YES — MCQ validation could be simplified to:
1. Question text exists and is non-empty
2. Correct answer exists and is non-empty
3. Then skip Rules 3, 4, 9, 10 (they'll be validated on real options after distractor insertion)

### YAGNI Violation: Attempt_num Uniqueness

Lines 267-269 use `attempt_num` to create unique placeholders:
```python
f'B) alt{attempt_num}a',  # alt0a, alt1a, alt2a
f'C) alt{attempt_num}b',  # alt0b, alt1b, alt2b
f'D) alt{attempt_num}c'   # alt0c, alt1c, alt2c
```

**Stated purpose** (from comments): "Use attempt_num to make placeholders unique across retries"

**Actual need**: None. Placeholders are discarded 20 lines later. Uniqueness across retries has zero business value because:
1. Each retry generates a NEW `q_data` dict
2. Placeholders are only used for validation in that attempt
3. They're replaced before storage
4. The validator doesn't cache or remember placeholders between retries

**Verdict**: Attempt_num uniqueness is YAGNI — "You Aren't Gonna Need It"

## Proposed Solutions

### Solution A: Skip MCQ Validation Entirely (RECOMMENDED)
**Approach**: For MCQ questions without options, skip the full validation pipeline. Only check core fields (question, answer), then generate real distractors before validation.

**New code flow**:
```python
# Generate question
q_data, model, prompt = question_generator.generate(...)

# For MCQ: validate core structure only
if q_type == 'mcq':
    if not q_data.get('question'):
        logger.warning('Generation attempt %d: empty question', attempt_num + 1)
        q_data = None
        continue
    if not q_data.get('correct_answer'):
        logger.warning('Generation attempt %d: empty answer', attempt_num + 1)
        q_data = None
        continue
else:
    # Non-MCQ: full validation
    is_valid, reason = validate_question(q_data, node_desc)
    if not is_valid:
        logger.warning('Validation rejected (attempt %d): %s', attempt_num + 1, reason)
        q_data = None
        continue

# Dedup checks (text-based, work on all types)
q_text = q_data['question'].strip()
if q_text in session_texts or q_text in global_correct_texts:
    logger.warning('Dedup rejected (attempt %d)', attempt_num + 1)
    q_data = None
    continue

# NOW generate real distractors for MCQ
if q_type == 'mcq' and q_data:
    q_data = insert_distractors(q_data)

# FINAL: validate MCQ options now that they're real
if q_type == 'mcq' and q_data:
    # Only validate MCQ-specific rules (3, 4, 9, 10)
    choices = q_data.get('options') or []
    if not validate_mcq_options(q_data, choices, node_desc):
        logger.warning('MCQ options rejected (attempt %d)', attempt_num + 1)
        q_data = None
        continue

break
```

**Pros**:
- Eliminates placeholder generation entirely (9 lines deleted)
- Single phase: generate → validate core → generate distractors → validate options
- Clear data flow, no temporary states
- Eliminates attempt_num uniqueness YAGNI
- Simpler to test and maintain

**Cons**:
- Reorders validation: core checks before distractors, option checks after
- Requires refactoring validator to separate MCQ-specific rules
- Slightly more code to extract `validate_mcq_options()`

**Effort**: Large (15-20 lines modified, 5+ lines in validator)
**Risk**: Medium (changes validation order; need thorough testing)

### Solution B: Keep Placeholders, Extract to Helper Function
**Approach**: Keep the two-phase pattern but extract placeholder generation to a dedicated function with clear documentation.

**Code**:
```python
def _create_mcq_placeholders(correct_answer, attempt_num):
    """Create temporary placeholder options for MCQ validation.

    These placeholders allow the validator to check structural rules
    (uniqueness, min count) before real distractors are computed.

    Attempt_num ensures unique placeholders if the question needs to be
    regenerated (prevents validator from seeing identical options twice).

    Returns list of 4 placeholder options.
    """
    return [
        f'A) {correct_answer}',
        f'B) placeholder_{attempt_num}_b',
        f'C) placeholder_{attempt_num}_c',
        f'D) placeholder_{attempt_num}_d',
    ]

# Usage at line 262-270:
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    q_data['options'] = _create_mcq_placeholders(correct, attempt_num)
```

**Pros**:
- Cleaner than inline code
- Documents intent explicitly
- Testable in isolation
- Easier to modify placeholder format

**Cons**:
- Doesn't eliminate the two-phase complexity
- Still creates and discards temporary data
- Doesn't address YAGNI violation of attempt_num uniqueness

**Effort**: Small (10 lines, extract function)
**Risk**: Low (refactoring only, no logic changes)

### Solution C: Validate MCQ-Specific Rules After Distractors
**Approach**: Keep placeholder generation but move MCQ-specific validation (Rules 3, 4, 9, 10) to AFTER distractor insertion.

**Code**:
```python
# Lines 262-270: Add placeholders as before

# Lines 272-288: Run ONLY non-MCQ rules on placeholders
if q_type != 'mcq':
    is_valid, reason = validate_question(q_data, node_desc)
    if not is_valid:
        q_data = None
        continue

# Lines 294-295: Generate real distractors
if q_type == 'mcq' and q_data:
    q_data = insert_distractors(q_data)

# NEW: Validate MCQ-specific rules on real distractors
if q_type == 'mcq' and q_data:
    is_valid, reason = validate_mcq_options(q_data, node_desc)
    if not is_valid:
        q_data = None
        continue

break
```

**Pros**:
- Validates MCQ rules on REAL distractors (more accurate)
- Keeps existing validator logic intact
- Moderate refactor

**Cons**:
- Still has placeholder generation
- More complex control flow

**Effort**: Medium (12-15 lines modified)
**Risk**: Medium (changes validation order)

## Recommended Action

Implement **Solution A** — simplify MCQ validation to skip full validation for questions without options, then validate real options after distractor insertion.

### Step 1: Refactor Validation Loop
Replace lines 259-291 with simplified logic:
- MCQ with no options: validate core fields only
- Non-MCQ: full validation
- Both: dedup checks
- MCQ: generate distractors, validate options

### Step 2: Extract MCQ Option Validator
Create new function in `engine/question_validator.py`:
```python
def validate_mcq_options(q_data, choices, node_description=''):
    """Validate MCQ-specific rules: uniqueness, answer in choices, length bias."""
    # Rules 3, 4, 9, 10 from validate_question()
    # Return (is_valid, reason)
```

### Step 3: Update Tests
Update test cases to reflect new validation order:
- Core field validation happens first
- Option validation happens after distractor insertion
- Ensure MCQ questions pass both stages

### Step 4: Verify No Regressions
```bash
python3 -m pytest tests/test_question_service.py -v
python3 -m pytest tests/test_question_validator.py -v
python3 -m pytest tests/ -v  # Full suite
```

## Acceptance Criteria

- [ ] Placeholder generation eliminated (Solution A) OR refactored cleanly (Solution B/C)
- [ ] MCQ validation simplified to core checks or moved to after distractor insertion
- [ ] All tests pass with new validation flow
- [ ] No loss of question quality (validate options still work)
- [ ] Code is simpler (net reduction of lines in generate_next)
- [ ] Attempt_num uniqueness pattern eliminated or justified with comment

## Technical Details

### Affected Files
- `services/question_service.py` (lines 259-295)
- `engine/question_validator.py` (new function or refactor)
- `tests/test_question_service.py` (update test expectations)

### Database Impact
None (data structure remains the same)

### Performance Impact
Negligible (might be slight improvement due to fewer checks)

## Institutional Learnings

**From learnings-researcher**: The three-stage MCQ pipeline (generate → validate → distract) was established in commit 915387c but could be optimized.

This refactoring aligns with DRY principle: don't create data you'll immediately discard.

## Work Log

- **2026-02-12**: Created todo after code review. Code-simplicity-reviewer and architecture-strategist flagged unnecessary two-phase pattern.

## Resources

- Commit 915387c: "Compute MCQ distractors algorithmically"
- YAGNI principle: https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it
- Related pattern: `ai/distractors.py` (distractor insertion logic)

---

**Status**: PENDING TRIAGE
**Priority**: P2 (IMPORTANT - Should Fix)
**Assigned to**: (none)
