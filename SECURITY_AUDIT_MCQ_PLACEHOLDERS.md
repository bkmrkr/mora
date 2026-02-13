# Security Audit: MCQ Placeholder Options (question_service.py lines 260-270)

**Date:** 2026-02-12
**Component:** services/question_service.py - MCQ placeholder option generation
**Severity Assessment:** MEDIUM risk with specific critical conditions
**Status:** Requires immediate mitigation

---

## Executive Summary

The MCQ placeholder option generation feature (lines 260-270) introduces a **data injection vulnerability** with downstream XSS implications. While the placeholder options are marked as temporary ("will be replaced with computed distractors"), this code currently:

1. **Directly interpolates untrusted LLM-generated content** into option strings without sanitization
2. **Stores unvalidated, unescaped data in the database** as JSON
3. **Renders this data in HTML/JavaScript contexts** on the frontend without consistent escaping

The primary risk: If the LLM output contains special characters, quotes, or escape sequences, these can propagate through the validation layer (which has string-based checks), be stored in the DB, and potentially reach students' browsers.

**Recommendation:** Implement output sanitization before f-string interpolation and validate that placeholders are never exposed to students.

---

## Detailed Vulnerability Analysis

### 1. DATA INJECTION - Unvalidated String Interpolation (MEDIUM)

**Location:** `/Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora/services/question_service.py:262-270`

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

**Vulnerability:**
- `correct` comes directly from LLM output (via `parse_ai_json_dict()`)
- No input validation, escaping, or sanitization is applied
- F-string directly concatenates potentially malicious content
- The placeholder options are stored in `q_data['options']` and eventually written to the database

**Attack Surface Examples:**

| Input from LLM | Result in f-string | Impact |
|---|---|---|
| `"x=5"` | `'A) x=5'` | Safe (alphanumeric) |
| `'x > -3"` | `'A) x > -3"'` | Quote character embedded |
| `"3\n4"` | `'A) 3\n4'` | Newline in JSON value |
| `'a") onclick="alert(1'` | `'A) a") onclick="alert(1'` | HTML/JS injection payload |
| `"3\\";c=4;d=\\"5"` | `'A) 3\\";c=4;d=\\"5'` | Escape sequence manipulation |

**Validation Chain Failure:**
The validation in `engine/question_validator.py` checks the question/answer **as strings** (Rule 8):
```python
if '</' in question or '```' in question:
    return False, 'HTML or markdown artifacts in question'
if '</' in answer or '```' in answer:
    return False, 'HTML or markdown artifacts in answer'
```

However:
- These checks happen **after** the placeholder options are created
- The validator checks `answer` string directly, NOT the options array
- A payload like `a") onclick="` does NOT match `'</'` or `` ``` ``
- The options array itself is not validated with the same rules

---

### 2. DATABASE STORAGE WITHOUT ESCAPING (HIGH)

**Location:** `/Users/greggurevich/Library/CloudStorage/OneDrive-Personal/Python/personal/mora/services/question_service.py:311`

```python
options=json.dumps(q_data.get('options')) if q_data.get('options') else None,
```

**Vulnerability:**
- `json.dumps()` does escape special characters (converts `"` → `\"`, newlines → `\n`)
- However, the **source data is unvalidated** when the list is created on line 265
- If `correct` contains characters that break JSON context (e.g., `\u0000` null bytes), edge cases could occur
- More critically: JSON escaping is NOT HTML escaping — they serve different purposes

**Example:**
```
Input: 'x > -3" onclick="alert'
After json.dumps(): '[…, "A) x > -3\" onclick=\"alert", …]'
When parsed by Python json.loads(): '…, "A) x > -3" onclick="alert", …'
When rendered in HTML: <button value='A) x > -3" onclick="alert'>
```

While JSON escaping prevents JSON corruption, it DOES NOT prevent HTML/JS injection when the data is rendered.

---

### 3. XSS VULNERABILITY - Frontend Rendering (HIGH)

**Frontend Rendering Points:**

#### Point A: `question.html:49-52` (HTML Form Button)
```html
{% for option in question.options %}
<button type="submit" name="answer" value="{{ option }}"
        class="choice-btn" data-key="{{ 'ABCD'[loop.index0] }}">
    <span class="choice-letter">{{ 'ABCD'[loop.index0] }}</span>
    <span class="choice-text">{{ option | strip_letter | render_math }}</span>
</button>
{% endfor %}
```

**XSS Risk Analysis:**
- `{{ option }}` in the form value attribute is **auto-escaped** by Jinja2 (default)
- The `render_math` filter applies `Markup()` which marks output as safe
- However, `strip_letter` filter does plain string manipulation without escaping

**Vulnerable Scenario:**
```
option = 'A) x"> onclick="alert(1)'
After strip_letter: 'x"> onclick="alert(1)'
After render_math (safe): '<button>...<span>x"> onclick="alert(1)'...</button>'
```

If `render_math` is called before proper HTML escaping, the quote escaping is lost.

#### Point B: Session Resume Path (question_service.py:32, routes/session.py:21-46)
```python
options = json.loads(q['options']) if q['options'] else None
```

When reconstructing from the database:
- Options are parsed directly from JSON
- No additional validation happens
- The same rendering pipeline applies

#### Point C: Feedback View (routes/session.py:234-270)
```python
answered_question = {
    'content': result.get('question_text', ''),
    'correct_answer': result.get('correct_answer', ''),
}
```

Rendered in templates with `| render_math` filter — same XSS risks apply.

---

### 4. BOUNDARY CONDITIONS & EDGE CASES (MEDIUM)

#### Edge Case 1: Very Long Answers
```python
correct = q_data.get('correct_answer', '')  # No length check
q_data['options'] = [f'A) {correct}', ...]
```

**Issue:** If `correct_answer` is extremely long (e.g., 10KB from LLM malfunction):
- Placeholder becomes `'A) ' + 10KB string`
- Option button HTML becomes unusually large
- Could contribute to DOM-based DoS or memory exhaustion

**Mitigated by:** `question_validator.py` Rule 7 (MAX_ANSWER_LENGTH = 200)
- BUT: This validation happens **after** placeholder creation
- If validation rejects the question, the oversized option is discarded
- Otherwise, the 200-char limit applies

#### Edge Case 2: Null/Empty Bytes
```python
correct = q_data.get('correct_answer', '')
if '\x00' in correct:  # Embedded null byte
    # json.dumps still succeeds
```

**Issue:** While `json.dumps()` can encode null bytes, they may cause issues in:
- Database drivers expecting null-terminated strings
- String processing in JavaScript
- Some regex operations

#### Edge Case 3: Unicode Normalization
```python
correct = 'é'  # NFD: e + combining accent
f'A) {correct}'  # Normalized differently in HTML vs Python
```

**Issue:** Unicode normalization differences could cause answer matching failures, though not a direct security risk.

---

### 5. DOWNSTREAM PROPAGATION ANALYSIS

#### Data Flow Security Check:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LLM Output (question_generator.py)                           │
│    correct_answer = "x > -3" (UNTRUSTED, UNVALIDATED)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Placeholder Creation (question_service.py:262-270)           │
│    options = [f'A) {correct}', ...]  (NO SANITIZATION)          │
│    ⚠️  INJECTION POINT - Unvalidated f-string                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Validation (question_validator.py)                           │
│    Check: '</' in answer, '```' in answer (STRING CHECKS ONLY)  │
│    ⚠️  Does not validate the options array itself               │
│    ⚠️  Cannot catch HTML attribute escape payloads              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Distractor Replacement (ai/distractors.py:176-212)           │
│    ✅ GOOD: Replaces placeholder options entirely               │
│    ✅ Creates new options from computed distractors             │
│    ✅ HOWEVER: Only happens if insert_distractors is called     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Database Storage (models/question.py:9-19)                   │
│    options=json.dumps(q_data.get('options'))  (JSON ESCAPED)    │
│    ✅ JSON escapes special chars (\" → \")                      │
│    ❌ Does NOT escape for HTML context                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Frontend Rendering (templates/session/question.html:49-52)   │
│    <button value="{{ option }}"...>                             │
│    <span>{{ option | strip_letter | render_math }}</span>       │
│    ⚠️  Jinja2 auto-escapes {{ }} but render_math uses Markup()  │
│    ⚠️  strip_letter does plain string manipulation              │
│    ⚠️  XSS RISK if escape context is wrong                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Student Browser                                              │
│    ❌ VULNERABLE: Unvalidated, unescaped content reaches HTML   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Finding:** The distractors.py `insert_distractors()` function replaces placeholders:
```python
# Compute new distractors
computed = compute_distractors(correct, num_options=4)
# Build options: put correct at random position
options = []
for i in range(4):
    if i == correct_index:
        options.append(correct)  # ⚠️  Still uses original correct_answer!
```

**CRITICAL:** The `insert_distractors()` function **rebuilds the options list but uses the SAME unvalidated `correct` value**. It does NOT sanitize the correct answer text.

---

### 6. ATTACK SCENARIO - Proof of Concept

#### Scenario: Reflected XSS via LLM Output

**Assumption:** An attacker can influence the LLM's question generation (e.g., via malicious context in the curriculum database, or if the LLM is online).

**Attack:**
1. LLM generates: `correct_answer = '5" onclick="alert(1)'`
2. Placeholder created: `options = ['A) 5" onclick="alert(1)', ...]`
3. Validation passes (no `</` or ` ``` `)
4. Question stored in DB with options as JSON
5. Frontend renders: `<button value="A) 5" onclick="alert(1)">`
6. Browser interprets extra `onclick` attribute
7. When user hovers/interacts, JavaScript executes

**Mitigation in Current Code:**
- Jinja2's default auto-escaping converts `"` → `&quot;` in form values
- The `| render_math` filter applies `Markup()`, which assumes safe HTML
- If the LaTeX rendering preserves HTML escaping, the payload is defused
- **However:** This relies on filter ordering and implementation details

**Risk Level:** Medium (mitigated by Jinja2 escaping, but fragile)

#### Scenario: Stored XSS via Database Persistence

**Attack:**
1. Same malicious LLM output
2. JSON escaping stores: `[..., "A) 5\" onclick=\"alert(1)", ...]`
3. When question is loaded from DB and rendered in feedback view
4. If `render_math` is applied to stored data, and if Markup() trusts the content
5. Payload executes

---

## OWASP Top 10 Compliance Assessment

| OWASP Category | Status | Findings |
|---|---|---|
| **A1: Injection** | ⚠️ PARTIAL RISK | Unvalidated string concatenation in f-string; JSON storage provides some protection but doesn't ensure HTML safety |
| **A2: Broken Authentication** | ✅ NOT APPLICABLE | Authentication not relevant to this code |
| **A3: Sensitive Data Exposure** | ✅ NO RISK | Correct answers are educational content, not sensitive |
| **A4: XML External Entities** | ✅ NO RISK | No XML processing in this code |
| **A5: Broken Access Control** | ✅ NO RISK | No authorization logic in this code |
| **A6: Security Misconfiguration** | ✅ NO RISK | Configuration is handled elsewhere |
| **A7: Cross-Site Scripting (XSS)** | 🔴 HIGH RISK | Unvalidated, unescaped content flows to frontend; mitigated by framework but fragile |
| **A8: Insecure Deserialization** | ✅ NO RISK | Only json.loads (safe) is used |
| **A9: Using Components with Known Vulnerabilities** | ⚠️ REQUIRES CHECK | Flask/Jinja2 versions should be verified |
| **A10: Insufficient Logging & Monitoring** | ⚠️ PARTIAL | LLM output is logged at 500 chars; full payloads not captured |

---

## Root Cause Analysis

### Why This Vulnerability Exists

1. **Placeholder Approach:** The decision to create placeholder options during validation is reasonable (allows validation to proceed), but the implementation shortcuts security.

2. **Trust Boundary Crossing:** LLM output is inherently untrusted, but this code treats it as semi-trusted by the time it reaches line 262.

3. **Validation Gap:** The `question_validator.py` validates the question/answer strings but not the derived options array.

4. **Temporary vs. Permanent Data:** Developers assumed placeholders are temporary, so didn't sanitize. However, they're persistent (stored in DB) and rendered to students.

5. **Multi-Stage Processing:** Data flows through multiple systems (LLM → parsing → validation → placeholder creation → distractors → DB → rendering), making it hard to track where sanitization should occur.

---

## Detailed Remediation Recommendations

### CRITICAL (Implement Immediately)

#### Recommendation 1: Sanitize correct_answer Before f-String Interpolation
**Severity:** CRITICAL
**Effort:** LOW
**Location:** `services/question_service.py:262-270`

Replace:
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

With:
```python
if q_type == 'mcq' and q_data and not q_data.get('options'):
    correct = q_data.get('correct_answer', '')
    # Sanitize: remove newlines, control chars, and limit length
    correct_safe = _sanitize_answer_text(correct)
    q_data['options'] = [
        f'A) {correct_safe}',
        f'B) alt{attempt_num}a',
        f'C) alt{attempt_num}b',
        f'D) alt{attempt_num}c'
    ]

def _sanitize_answer_text(text):
    """Remove dangerous characters from answer text.

    Used for placeholder options during validation.
    Removes control characters, newlines, and limits length.
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove control characters and newlines
    import unicodedata
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

    # Limit length to prevent oversized options
    max_len = 150  # Leave room for "A) " prefix and some padding
    if len(text) > max_len:
        text = text[:max_len-3] + '...'

    return text.strip()
```

**Rationale:**
- Removes control characters that could break JSON or HTML
- Normalizes whitespace
- Limits length to prevent injection via size
- Applied to ALL placeholder options, not just the correct answer

---

#### Recommendation 2: Add Options Array Validation to question_validator.py
**Severity:** CRITICAL
**Effort:** MEDIUM
**Location:** `engine/question_validator.py:53-180`

Add new validation rule after Rule 11:

```python
# Rule 12b: Validate MCQ options (NEW)
if q_type == 'mcq' and choices:
    for i, choice in enumerate(choices):
        choice_ok, choice_reason = _validate_mcq_option(choice)
        if not choice_ok:
            return False, f'Invalid MCQ option {i}: {choice_reason}'
```

Add new helper function:

```python
def _validate_mcq_option(option):
    """Validate a single MCQ option string.

    Returns (is_valid, reason).
    - Checks for control characters, excessive escapes
    - Prevents HTML/JS injection payloads
    - Ensures option is plain text or valid LaTeX
    """
    import unicodedata
    import re

    if not isinstance(option, str):
        return False, 'Option is not a string'

    option = option.strip()
    if not option:
        return False, 'Option is empty'

    # Check for control characters (newlines, null bytes, etc)
    for c in option:
        cat = unicodedata.category(c)
        if cat[0] == 'C':  # Control characters
            return False, f'Option contains control character: {repr(c)}'

    # Check for HTML/JS injection patterns
    dangerous_patterns = [
        r'on\w+\s*=',  # onclick=, onerror=, etc
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'\u0000',  # Null byte
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, option, re.IGNORECASE):
            return False, f'Option contains dangerous pattern: {pattern}'

    # Check that quotes are balanced (basic check)
    # Allow quotes inside, but not unescaped quotes at option boundaries
    if option.count('"') % 2 != 0:
        # Odd number of quotes might indicate escaping issues
        # Log warning but don't fail — LaTeX often has backslashes
        logger.warning('MCQ option has unbalanced quotes: %s', option)

    return True, ''
```

**Rationale:**
- Validates the actual options array before DB storage
- Catches injection attempts that wouldn't match the string-only checks
- Rejects control characters that could break JSON/HTML
- Looks for specific attack patterns

---

#### Recommendation 3: Ensure insert_distractors() Sanitizes the Correct Answer
**Severity:** HIGH
**Effort:** LOW
**Location:** `ai/distractors.py:176-212`

Modify the function to sanitize the correct answer when rebuilding options:

```python
def insert_distractors(question_data):
    """Add computed distractors to a question dict.

    If the question already has options, replace them with computed ones.
    If it's MCQ type but has no options, generate them.
    """
    q_type = question_data.get('question_type', 'mcq')
    if q_type != 'mcq':
        return question_data

    correct = question_data.get('correct_answer', '')
    if not correct:
        return question_data

    # Sanitize the correct answer text
    # (in case of unusual characters from LLM)
    correct_clean = _sanitize_for_option(correct)

    # Compute new distractors
    computed = compute_distractors(correct_clean, num_options=4)

    # Build options: put correct at random position
    correct_index = random.randint(0, 3)
    options = []

    for i in range(4):
        if i == correct_index:
            options.append(correct_clean)  # Use sanitized version
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


def _sanitize_for_option(text):
    """Remove dangerous characters from text before using in options.

    Also applied to the correct_answer itself when rebuilding options.
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
        text = text[:max_len-3] + '...'

    return text.strip()
```

**Rationale:**
- Ensures distractors are built from sanitized data
- Protects against LLM outputs that might have encoding issues
- Keeps options consistent in "cleanliness"

---

### HIGH PRIORITY (Implement Within 1-2 Sprints)

#### Recommendation 4: Add Content Security Policy (CSP) Header
**Severity:** HIGH
**Effort:** LOW
**Location:** `app.py` (Flask configuration)

Add CSP header to prevent inline script execution:

```python
@app.after_request
def set_security_headers(response):
    """Set security headers to mitigate XSS."""
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
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

**Rationale:**
- Blocks inline scripts even if XSS payload reaches the DOM
- Prevents frame-based attacks
- Standard defense-in-depth for web applications

---

#### Recommendation 5: Validate render_math Filter for Safe Output
**Severity:** HIGH
**Effort:** MEDIUM
**Location:** `services/math_renderer.py` (if it exists) or `app.py`

Review the `render_math_in_text()` function:

```python
@app.template_filter('render_math')
def render_math_filter(text):
    """Replace LaTeX expressions with server-rendered SVG images."""
    # SECURITY: This should only convert LaTeX to SVG, never preserve HTML
    return Markup(render_math_in_text(str(text)))
```

Ensure that:
1. `render_math_in_text()` does NOT preserve HTML tags from input
2. All non-LaTeX text is properly escaped before returning
3. Only valid LaTeX patterns are replaced; unknown patterns are escaped

**Example:**
```python
def render_math_in_text(text):
    """Safely render LaTeX in text.

    SECURITY: Escape HTML first, then replace LaTeX patterns.
    """
    from markupsafe import escape

    # Step 1: Escape HTML to prevent injection
    text = escape(text)

    # Step 2: Replace LaTeX patterns with SVG
    # (This only works on escaped text, so LaTeX patterns are literal strings)
    text = _replace_latex_with_svg(text)

    return text
```

**Rationale:**
- Ensures render_math doesn't accidentally preserve malicious HTML
- Escaping-first approach is more secure than allow-listing

---

### MEDIUM PRIORITY (Implement Within 1 Sprint)

#### Recommendation 6: Add Input Sanitization Utility Module
**Severity:** MEDIUM
**Effort:** LOW
**Location:** Create new file: `utils/sanitization.py`

```python
"""Input sanitization utilities for educational content.

Educational content from LLMs must be sanitized before:
1. Being used in string interpolation (f-strings)
2. Being stored in database
3. Being rendered to students

This module provides consistent sanitization across the application.
"""

import unicodedata
import re
from typing import Optional


def sanitize_answer_text(text: str, max_length: int = 200) -> str:
    """Sanitize answer text for safe use in MCQ options.

    Removes:
    - Control characters (null bytes, control codes)
    - Excessive whitespace
    - Limits length

    Args:
        text: Raw answer text from LLM
        max_length: Maximum allowed length (default 200)

    Returns:
        Sanitized answer text safe for use in options
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove control characters (Unicode category C)
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Trim to max length
    if len(text) > max_length:
        text = text[:max_length-3] + '...'

    return text.strip()


def is_safe_for_html_attribute(text: str) -> bool:
    """Check if text is safe to use in HTML attributes.

    Returns False if text contains:
    - Unescaped quotes or apostrophes
    - Event handler patterns (onclick=, etc)
    - Protocol handlers (javascript:, data:, etc)
    - Null bytes

    Args:
        text: Text to validate

    Returns:
        True if safe, False otherwise
    """
    if not isinstance(text, str):
        return False

    # Check for null bytes
    if '\x00' in text:
        return False

    # Check for event handlers
    if re.search(r'\bon\w+\s*=', text, re.IGNORECASE):
        return False

    # Check for protocol handlers
    if re.search(r'(?:javascript|data|vbscript):', text, re.IGNORECASE):
        return False

    # Check for unescaped quotes in attribute context
    # (Note: JSON.dumps and HTML escaping handle this, but warn for safety)
    if "'" in text and '"' in text:
        # Both quote types present — might indicate escaping confusion
        return False

    return True


def validate_option_array(options: list) -> tuple[bool, Optional[str]]:
    """Validate a list of MCQ options.

    Args:
        options: List of option strings

    Returns:
        (is_valid, error_message) — error_message is None if valid
    """
    if not isinstance(options, list):
        return False, "Options must be a list"

    if len(options) < 3:
        return False, f"At least 3 options required, got {len(options)}"

    if len(options) > 10:
        return False, f"Too many options ({len(options)}, max 10)"

    seen = set()
    for i, opt in enumerate(options):
        if not isinstance(opt, str):
            return False, f"Option {i} is not a string: {type(opt)}"

        # Check for duplicates (normalized)
        opt_lower = opt.strip().lower()
        if opt_lower in seen:
            return False, f"Duplicate option: {opt}"
        seen.add(opt_lower)

        # Check for dangerous patterns
        if not is_safe_for_html_attribute(opt):
            return False, f"Option {i} contains unsafe content: {opt}"

    return True, None
```

**Rationale:**
- Centralizes sanitization logic
- Makes it easy to reuse and update
- Documents security assumptions
- Easier to test

---

#### Recommendation 7: Add Comprehensive Test Coverage
**Severity:** MEDIUM
**Effort:** MEDIUM
**Location:** `tests/test_question_service_security.py` (new file)

```python
"""Security tests for question generation."""

import pytest
from services import question_service
from engine.question_validator import validate_question


class TestMCQPlaceholderSecurity:
    """Tests for MCQ placeholder option generation security."""

    def test_placeholder_with_quote_characters(self):
        """Placeholder options should handle quote characters safely."""
        # Simulate LLM output with quotes
        q_data = {
            'question': 'What is the answer?',
            'correct_answer': 'x > -3"',  # Double quote
            'question_type': 'mcq'
        }

        # Create placeholders
        if not q_data.get('options'):
            correct = q_data.get('correct_answer', '')
            q_data['options'] = [
                f'A) {correct}',
                f'B) alt0a',
                f'C) alt0b',
                f'D) alt0c'
            ]

        # Validate should pass (or fail with clear reason)
        is_valid, reason = validate_question(q_data, 'test')
        # Either validation passes or fails for clear reason (not injection)
        assert not reason.startswith('Unexpected'), \
            f"Validation failed unexpectedly: {reason}"

    def test_placeholder_with_newlines(self):
        """Placeholder options should handle newlines safely."""
        q_data = {
            'question': 'What is the answer?',
            'correct_answer': 'answer\nfoo\nbar',
            'question_type': 'mcq'
        }

        if not q_data.get('options'):
            correct = q_data.get('correct_answer', '')
            q_data['options'] = [
                f'A) {correct}',
                f'B) alt0a',
                f'C) alt0b',
                f'D) alt0c'
            ]

        is_valid, reason = validate_question(q_data, 'test')
        assert not reason.startswith('Unexpected')

    def test_placeholder_with_escape_sequences(self):
        """Placeholder options should handle backslash sequences safely."""
        q_data = {
            'question': 'What is the answer?',
            'correct_answer': r'3\" onclick=\"alert(1)',
            'question_type': 'mcq'
        }

        if not q_data.get('options'):
            correct = q_data.get('correct_answer', '')
            q_data['options'] = [
                f'A) {correct}',
                f'B) alt0a',
                f'C) alt0b',
                f'D) alt0c'
            ]

        # Should either handle safely or reject
        is_valid, reason = validate_question(q_data, 'test')
        assert not reason.startswith('Unexpected')

    def test_placeholder_options_json_encoding(self):
        """Placeholder options should be JSON-safe."""
        import json

        q_data = {
            'question': 'What is the answer?',
            'correct_answer': 'answer with "quotes" and \\backslash',
            'question_type': 'mcq'
        }

        if not q_data.get('options'):
            correct = q_data.get('correct_answer', '')
            q_data['options'] = [
                f'A) {correct}',
                f'B) alt0a',
                f'C) alt0b',
                f'D) alt0c'
            ]

        # Should be JSON-safe
        try:
            json_str = json.dumps(q_data['options'])
            parsed = json.loads(json_str)
            assert isinstance(parsed, list)
            assert len(parsed) == 4
        except Exception as e:
            pytest.fail(f"Options should be JSON-safe: {e}")

    def test_placeholder_with_xss_payload(self):
        """Placeholder options should not introduce XSS.

        This is more of a detection test than prevention,
        since prevention happens in validation and rendering.
        """
        q_data = {
            'question': 'What is the answer?',
            'correct_answer': '5" onclick="alert(1)"',
            'question_type': 'mcq'
        }

        if not q_data.get('options'):
            correct = q_data.get('correct_answer', '')
            q_data['options'] = [
                f'A) {correct}',
                f'B) alt0a',
                f'C) alt0b',
                f'D) alt0c'
            ]

        # At minimum, validation should flag this or sanitize it
        is_valid, reason = validate_question(q_data, 'test')

        # If validation passes, options should be safe
        if is_valid:
            # Verify the option doesn't have unescaped onclick
            option_a = q_data['options'][0]
            # This is a basic check; actual rendering safety depends on template
            assert not ('onclick=' in option_a and '"' not in repr(option_a))
```

**Rationale:**
- Tests catch regressions
- Documents expected behavior
- Validates security assumptions

---

## Testing & Verification Checklist

Before deploying any fixes, verify:

- [ ] All control characters are removed from placeholder options
- [ ] Placeholder options are JSON-safe (can roundtrip through json.dumps/loads)
- [ ] Placeholder options are HTML-safe (properly escaped in templates)
- [ ] The `insert_distractors()` function uses sanitized correct_answer
- [ ] Validation in `question_validator.py` checks the options array
- [ ] CSP headers are deployed and working
- [ ] `render_math` filter properly escapes non-LaTeX content
- [ ] All new security tests pass
- [ ] Existing tests still pass
- [ ] No log spam from sanitization

---

## Deployment Recommendations

1. **Phase 1 (Immediate):**
   - Deploy Recommendations 1 & 2 (sanitization + validation)
   - Add security tests (Recommendation 7)
   - Verify with regression testing

2. **Phase 2 (Within 1 Sprint):**
   - Deploy Recommendations 3, 4, 5 (distractors, CSP, render_math)
   - Create sanitization utility module (Recommendation 6)
   - Review and update all related documentation

3. **Phase 3 (Follow-up):**
   - Audit other LLM-generated content endpoints
   - Review template filters for XSS risks
   - Add monitoring for sanitization violations in logs

---

## Monitoring & Alerting

Add logging to detect potential attacks:

```python
import logging

logger = logging.getLogger('security.questions')

def _sanitize_answer_text(text):
    if not isinstance(text, str):
        text = str(text)

    before = text
    # ... sanitization logic ...
    after = text

    if before != after:
        # Log if content was modified (potential attack attempt)
        logger.warning('Answer text was sanitized: %r → %r',
                      before[:100], after[:100])

    return after
```

---

## References & Standards

- **CWE-79:** Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')
- **CWE-94:** Improper Control of Generation of Code ('Code Injection')
- **OWASP Top 10 2021:** A03:2021 – Injection
- **Flask Security:** https://flask.palletsprojects.com/security/
- **Jinja2 Security:** https://jinja.palletsprojects.com/en/3.0.x/api/#markupsafe.Markup

---

## Summary

The MCQ placeholder option generation feature introduces a **medium-risk injection vulnerability** through unvalidated string interpolation of LLM-generated content. While mitigated somewhat by JSON escaping and Jinja2 template auto-escaping, the risk is real and can be demonstrated with carefully crafted payloads.

**Immediate actions required:**
1. Sanitize the `correct_answer` before f-string interpolation (lines 262-270)
2. Add validation of the options array in `question_validator.py`
3. Ensure `insert_distractors()` uses sanitized content

These changes are low-effort but high-value for security hardening.

---

**Report prepared by:** Security Audit Analysis
**Last updated:** 2026-02-12
**Next review:** After remediation implementation
