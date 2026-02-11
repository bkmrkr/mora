"""Grade open-ended answers using Ollama."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json

logger = logging.getLogger(__name__)

GRADING_PROMPT = """You are grading a student's answer. Compare it to the correct answer.

Return ONLY valid JSON:
{
  "is_correct": true,
  "partial_score": 0.85,
  "feedback": "Explanation of what was right/wrong"
}

Be generous with partial credit for answers that show understanding.
Return ONLY the JSON, no other text."""


def grade(question_text, correct_answer, student_answer, node_description):
    """Grade an open-ended answer via Ollama.

    Returns (is_correct, partial_score, feedback, model, prompt).
    """
    user_prompt = f"""Question: {question_text}
Correct answer: {correct_answer}
Student answer: {student_answer}
Topic context: {node_description}

Grade this answer. Return JSON only."""

    text, model, prompt = ask(GRADING_PROMPT, user_prompt, temperature=0.3)
    result = parse_ai_json(text)

    is_correct = bool(result.get('is_correct', False))
    partial_score = float(result.get('partial_score', 1.0 if is_correct else 0.0))
    feedback = result.get('feedback', '')

    return is_correct, partial_score, feedback, model, prompt
