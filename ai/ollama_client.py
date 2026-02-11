"""Ollama HTTP client for local LLM inference."""
import json
import logging
import time
import urllib.request
import urllib.error

from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


def ask(system_prompt, user_prompt, max_tokens=512, temperature=0.7):
    """Send a chat completion request to Ollama.

    Returns (response_text, model_used, full_prompt).
    """
    full_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    data = json.dumps({
        'model': OLLAMA_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'stream': False,
        'think': False,
        'keep_alive': '30m',
        'options': {
            'num_predict': max_tokens,
            'temperature': temperature,
        },
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=data,
        headers={'Content-Type': 'application/json'},
    )

    try:
        t0 = time.monotonic()
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        elapsed = time.monotonic() - t0
        text = result.get('message', {}).get('content', '')
        model = result.get('model', OLLAMA_MODEL)
        eval_count = result.get('eval_count', 0)
        logger.info('Ollama %s — %d chars, %d tokens, %.1fs',
                     model, len(text), eval_count, elapsed)
        return text, model, full_prompt
    except urllib.error.URLError as e:
        logger.error('Ollama request failed: %s', e)
        raise ConnectionError(f"Cannot reach Ollama at {OLLAMA_BASE_URL}: {e}") from e
