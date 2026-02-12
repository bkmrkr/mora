"""Parse JSON from AI responses, handling markdown code blocks."""
import json
import re


def _fix_latex_escapes(text):
    r"""Fix invalid JSON escape sequences from LLM output (LaTeX, etc.).

    Only called after json.loads() has already failed, confirming the text
    contains invalid escapes. LLMs produce LaTeX like \(\sqrt{16}\) and
    \times inside JSON string values — these are invalid JSON escapes.

    Strategy: walk the text character by character. For every \X sequence:
    - Keep \" (JSON string delimiter — must stay)
    - Keep \\ (already escaped backslash)
    - Double-escape everything else: \( → \\(, \t → \\t, \s → \\s
      This treats them as literal characters, not JSON escapes.
    """
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '\\' and i + 1 < n:
            next_char = text[i + 1]
            if next_char == '"':
                # \" is structural JSON — preserve
                result.append('\\"')
                i += 2
            elif next_char == '\\':
                # \\ already escaped — preserve
                result.append('\\\\')
                i += 2
            else:
                # Invalid or ambiguous escape (\t, \n, \(, \s, etc.)
                # Double the backslash so json.loads treats it as literal
                result.append('\\\\')
                result.append(next_char)
                i += 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def parse_ai_json(text):
    """Extract and parse JSON from LLM response text.

    Handles:
    - Raw JSON
    - JSON wrapped in ```json ... ``` blocks
    - JSON wrapped in ``` ... ``` blocks
    - Invalid escape sequences from LaTeX (e.g. \\( \\) \\sqrt \\times)
    """
    cleaned = text.strip()

    # Try raw parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try with fixed LaTeX escapes
    try:
        return json.loads(_fix_latex_escapes(cleaned))
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', cleaned, re.DOTALL)
    if match:
        block = match.group(1).strip()
        for attempt_text in [block, _fix_latex_escapes(block)]:
            try:
                return json.loads(attempt_text)
            except json.JSONDecodeError:
                continue

    # Try to find JSON object or array in the text
    for pattern in [r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', r'\[.*\]']:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            raw = match.group(0)
            for attempt_text in [raw, _fix_latex_escapes(raw)]:
                try:
                    return json.loads(attempt_text)
                except json.JSONDecodeError:
                    continue

    raise json.JSONDecodeError("No valid JSON found in response", cleaned, 0)


def parse_ai_json_dict(text):
    """Parse JSON from LLM response, guaranteeing a dict return.

    If the LLM returns a JSON array, extracts the first dict element.
    Raises ValueError if result cannot be coerced to a dict.
    """
    result = parse_ai_json(text)
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                return item
        raise ValueError(
            f"LLM returned JSON array with no dict elements: {text[:300]}"
        )
    raise ValueError(
        f"LLM returned {type(result).__name__}, expected dict: {text[:300]}"
    )
