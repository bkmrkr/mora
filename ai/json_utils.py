"""Parse JSON from AI responses, handling markdown code blocks."""
import json
import re


def parse_ai_json(text):
    """Extract and parse JSON from LLM response text.

    Handles:
    - Raw JSON
    - JSON wrapped in ```json ... ``` blocks
    - JSON wrapped in ``` ... ``` blocks
    """
    cleaned = text.strip()

    # Try raw parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object or array in the text
    for pattern in [r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', r'\[.*\]']:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
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
        raise ValueError(f"LLM returned JSON array with no dict elements")
    raise ValueError(f"LLM returned {type(result).__name__}, expected dict")
