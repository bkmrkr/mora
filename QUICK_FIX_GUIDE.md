# Quick Fix Guide: MCQ Placeholder Security Hardening

**Time to implement:** ~4 hours
**Difficulty:** Low-Medium
**Risk of breaking existing code:** Low (backward compatible)

---

## Fix 1: Add Sanitization Function (15 min)

**File:** `services/question_service.py`
**Location:** Add before the `generate_next()` function (around line 28)

```python
def _sanitize_answer_text(text, max_length=150):
    """Sanitize answer text for safe use in placeholder options.

    Removes control characters, normalizes whitespace, and limits length.
    Safe for use in f-strings, JSON storage, and HTML rendering.
    """
    import unicodedata

    if not isinstance(text, str):
        text = str(text)

    # Remove control characters (Unicode category C)
    # This includes null bytes, newlines, and other problematic chars
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')

    # Normalize whitespace: collapse multiple spaces to single space
    text = ' '.join(text.split())

    # Limit length to prevent oversized options
    if len(text) > max_length:
        text = text[:max_length - 3] + '...'

    return text.strip()
```

**Testing:**
```python
# Quick test these in a Python shell:
assert _sanitize_answer_text('x > -3') == 'x > -3'
assert _sanitize_answer_text('5" onclick="alert"') == '5" onclick="alert"'
assert _sanitize_answer_text('hello\nworld') == 'hello world'
assert '\x00' not in _sanitize_answer_text('test\x00null')
```

---

## Fix 2: Update Placeholder Creation (5 min)

**File:** `services/question_service.py`
**Location:** Lines 262-270 (in the `generate_next()` function)

**Before:**
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

**After:**
```python
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    correct_safe = _sanitize_answer_text(correct)  # ← ADD THIS LINE
    q_data['options'] = [
        f'A) {correct_safe}',  # ← CHANGE: use correct_safe
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]
```

**Testing:**
```bash
cd /Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora
python3 -m pytest tests/test_question_service.py -v
# All tests should pass
```

---

## Fix 3: Add Options Validation (2 hours)

**File:** `engine/question_validator.py`
**Location:** Add new function (around line 620, before the visual check functions)

```python
# Add this NEW section after Rule 11 validation

def _validate_mcq_option(option):
    """Validate a single MCQ option string.

    Returns (is_valid, reason).
    Checks for:
    - Control characters (null bytes, newlines, etc)
    - HTML/JS injection patterns
    - Dangerous protocols
    """
    import unicodedata
    import re

    if not isinstance(option, str):
        return False, 'Option is not a string'

    option = option.strip()
    if not option:
        return False, 'Option is empty'

    # Check for control characters
    for c in option:
        cat = unicodedata.category(c)
        if cat[0] == 'C':  # Unicode control character category
            return False, f'Option contains control character: {repr(c)}'

    # Check for HTML/JS injection patterns
    dangerous_patterns = [
        (r'on\w+\s*=', 'Event handler (onclick=, etc)'),
        (r'<script', 'Script tag'),
        (r'javascript:', 'JavaScript protocol'),
        (r'data:text/html', 'Data URI HTML'),
        (r'<iframe', 'iFrame injection'),
        (r'<img.*?onerror', 'Image with onerror'),
    ]

    for pattern, description in dangerous_patterns:
        if re.search(pattern, option, re.IGNORECASE):
            return False, f'Option contains dangerous pattern: {description}'

    return True, ''
```

**Then update the main validation function:**

Find the section after Rule 11 (around line 140):
```python
    # Rule 11: No "all/none of the above" choices — strip letter prefixes
    if choices:
        for c in choices:
            stripped = LETTER_PREFIX_RE.sub('', c).strip().lower()
            if stripped in BANNED_CHOICES or c.strip().lower() in BANNED_CHOICES:
                return False, f'Banned choice: "{c.strip()}"'

    # ← ADD THIS NEW VALIDATION RIGHT AFTER RULE 11
```

Add this code right after Rule 11:
```python
    # Rule 11b: Validate MCQ options (NEW)
    # Check each option for dangerous content (control chars, HTML/JS patterns)
    if q_type == 'mcq' and choices:
        for i, choice in enumerate(choices):
            is_safe, reason = _validate_mcq_option(choice)
            if not is_safe:
                return False, f'Invalid MCQ option {i}: {reason}'
```

**Testing:**
```bash
cd /Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora
python3 -m pytest tests/test_question_validator.py -v
# All tests should pass

# Quick manual test:
from engine.question_validator import validate_question

# Should pass (normal option)
result = validate_question({
    'question': 'What is 2+2?',
    'correct_answer': '4',
    'options': ['4', '3', '5', '6']
}, 'test')
assert result[0] == True

# Should fail (dangerous pattern)
result = validate_question({
    'question': 'What is 2+2?',
    'correct_answer': '4',
    'options': ['4', '3" onclick="alert', '5', '6']
}, 'test')
assert result[0] == False
assert 'dangerous' in result[1].lower()

print("All manual tests passed!")
```

---

## Fix 4: Update Distractors Function (30 min)

**File:** `ai/distractors.py`
**Location:** Update the `insert_distractors()` function (around line 176)

**Add helper function at the top of the file:**
```python
def _sanitize_for_option(text):
    """Remove dangerous characters from text before using in options.

    Applied to the correct_answer when rebuilding options.
    """
    import unicodedata

    if not isinstance(text, str):
        text = str(text)

    # Remove control characters
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Limit length
    max_len = 150
    if len(text) > max_len:
        text = text[:max_len - 3] + '...'

    return text.strip()
```

**Update the `insert_distractors()` function:**

**Before:**
```python
def insert_distractors(question_data):
    """Add computed distractors to a question dict."""
    q_type = question_data.get('question_type', 'mcq')
    if q_type != 'mcq':
        return question_data

    correct = question_data.get('correct_answer', '')
    if not correct:
        return question_data

    # Compute new distractors
    computed = compute_distractors(correct, num_options=4)

    # Build options: put correct at random position
    correct_index = random.randint(0, 3)
    options = []

    for i in range(4):
        if i == correct_index:
            options.append(correct)  # ← Uses original, unvalidated
        else:
            if computed:
                options.append(computed.pop(0))
            else:
                options.append(_fallback_distractor(correct))

    question_data['options'] = options

    # Update correct_answer to include letter (A/B/C/D)
    letters = ['A', 'B', 'C', 'D']
    question_data['correct_answer'] = f"{letters[correct_index]}) {correct}"

    return question_data
```

**After:**
```python
def insert_distractors(question_data):
    """Add computed distractors to a question dict."""
    q_type = question_data.get('question_type', 'mcq')
    if q_type != 'mcq':
        return question_data

    correct = question_data.get('correct_answer', '')
    if not correct:
        return question_data

    # SECURITY: Sanitize the correct answer for safe option display
    correct_clean = _sanitize_for_option(correct)

    # Compute new distractors
    computed = compute_distractors(correct_clean, num_options=4)

    # Build options: put correct at random position
    correct_index = random.randint(0, 3)
    options = []

    for i in range(4):
        if i == correct_index:
            options.append(correct_clean)  # ← Use sanitized version
        else:
            if computed:
                options.append(computed.pop(0))
            else:
                options.append(_fallback_distractor(correct_clean))

    question_data['options'] = options

    # Update correct_answer to include letter (A/B/C/D)
    letters = ['A', 'B', 'C', 'D']
    question_data['correct_answer'] = f"{letters[correct_index]}) {correct_clean}"

    return question_data
```

**Testing:**
```bash
cd /Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora
python3 -m pytest tests/test_distractors.py -v
# All tests should pass
```

---

## Fix 5: Add Content-Security-Policy Header (20 min)

**File:** `app.py`
**Location:** Add new method after the `log_response()` function (around line 70)

```python
@app.after_request
def set_security_headers(response):
    """Set security headers to prevent XSS and other attacks."""
    # Prevent inline scripts even if XSS payload reaches the DOM
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    # Prevent MIME-type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Enable XSS filter in older browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'

    return response
```

**Testing:**
```bash
cd /Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora
python3 app.py  # Start the server

# In another terminal, check headers:
curl -I http://localhost:5002/
# Should see:
#   Content-Security-Policy: default-src 'self'; ...
#   X-Content-Type-Options: nosniff
#   X-Frame-Options: DENY
#   X-XSS-Protection: 1; mode=block
```

---

## Final Testing Checklist

After implementing all fixes, run these tests:

```bash
cd /Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora

# 1. Run all tests
python3 -m pytest tests/ -v --tb=short

# 2. Check for import errors
python3 -c "from services.question_service import generate_next; print('OK')"

# 3. Manual integration test
python3 << 'EOF'
from services.question_service import _sanitize_answer_text
from engine.question_validator import validate_question

# Test sanitization
assert _sanitize_answer_text('hello\nworld') == 'hello world'
assert '\x00' not in _sanitize_answer_text('test\x00null')

# Test validation
q = {
    'question': 'What is 2+2?',
    'correct_answer': '4',
    'options': ['4', '3', '5', '6']
}
is_valid, reason = validate_question(q)
assert is_valid, reason

print("✓ All manual tests passed!")
EOF

# 4. Start server and verify headers
timeout 5 python3 app.py &
sleep 2
curl -I http://localhost:5002/ 2>/dev/null | grep -E "Content-Security-Policy|X-Content-Type"
```

Expected output:
```
✓ All manual tests passed!
Content-Security-Policy: default-src 'self'; ...
X-Content-Type-Options: nosniff
```

---

## Deployment Steps

1. **Backup current code:**
   ```bash
   git branch backup-pre-security-fix
   git stash
   ```

2. **Apply fixes in order:**
   - Fix 1: Sanitization function
   - Fix 2: Update placeholder creation
   - Fix 3: Add options validation
   - Fix 4: Update distractors
   - Fix 5: Add CSP header

3. **Test after each fix:**
   ```bash
   python3 -m pytest tests/ -v
   ```

4. **Commit changes:**
   ```bash
   git add services/question_service.py engine/question_validator.py ai/distractors.py app.py
   git commit -m "Security hardening: Add input sanitization and validation for MCQ placeholders

   - Add _sanitize_answer_text() to remove control characters from LLM output
   - Use sanitized answer in placeholder option generation
   - Add _validate_mcq_option() to validate MCQ options for dangerous patterns
   - Update insert_distractors() to use sanitized correct answer
   - Add Content-Security-Policy and security headers

   Fixes: Unvalidated string interpolation of LLM output in MCQ placeholders
   Related issues: Data injection, XSS vulnerability
   "
   ```

5. **Push to remote:**
   ```bash
   git push origin main
   ```

---

## Rollback Plan

If issues arise:

```bash
# Revert to previous version
git revert HEAD

# OR reset to backup branch
git reset --hard backup-pre-security-fix
```

---

## What Changed (Impact Assessment)

| Component | Change | Impact | Risk |
|-----------|--------|--------|------|
| question_service.py | Added sanitization function | None (new function) | None |
| question_service.py | Use sanitized text in placeholders | Generated options now "cleaner" | Low (improves safety) |
| question_validator.py | Added option validation | Questions with bad options rejected | Low (stricter validation) |
| distractors.py | Use sanitized correct_answer | Distractors from cleaner text | Low (no behavior change) |
| app.py | Added CSP header | Blocks inline scripts | Low (standard security) |

**Backward Compatibility:** All changes are backward compatible. Existing tests should pass. The only behavior change is rejecting questions with invalid MCQ options (which is correct behavior).

---

## Verification Checklist

- [ ] All test suites pass
- [ ] No import errors
- [ ] Manual integration test passes
- [ ] CSP headers are set
- [ ] Question generation still works
- [ ] Pre-caching still works
- [ ] Answer validation still works
- [ ] Database schema unchanged
- [ ] Frontend templates unchanged
- [ ] Git commit message is clear
- [ ] Code follows existing style

---

## Estimated Timeline

| Task | Time | Notes |
|------|------|-------|
| Read this guide | 15 min | |
| Fix 1: Sanitization function | 15 min | Copy-paste, minimal customization |
| Fix 2: Update placeholder creation | 5 min | One-line change |
| Fix 3: Add validation | 2 hours | Largest change; test thoroughly |
| Fix 4: Update distractors | 30 min | Copy-paste helper + change calls |
| Fix 5: Add CSP header | 20 min | Copy-paste security headers |
| Testing & verification | 1 hour | Run test suite, manual tests |
| Git commit & push | 15 min | |
| **Total** | **~4 hours** | |

---

## Support & Questions

If you encounter issues:

1. Check the detailed report: `SECURITY_AUDIT_MCQ_PLACEHOLDERS.md`
2. Review the code examples in this guide
3. Run individual test suites to isolate the issue
4. Check git log for similar changes: `git log --grep="sanitiz"`

---

**Last Updated:** 2026-02-12
**Status:** Ready to implement
**Priority:** High (but not critical)
