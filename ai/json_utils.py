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
