"""Generate explanations for wrong answers."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json

logger = logging.getLogger(__name__)

EXPLAIN_PROMPT = """You are a patient tutor explaining a concept after a wrong answer.

Return ONLY valid JSON:
{
  "encouragement": "Brief positive message",
  "explanation": "Clear step-by-step explanation of the correct solution",
  "key_concept": "The core concept the student should understand",
  "tip": "A practical tip for similar questions"
}

Return ONLY the JSON, no other text."""


def explain(question_text, correct_answer, student_answer,
            node_name, node_description):
    """Generate an explanation for a wrong answer.

    Returns (explanation_dict, model, prompt).
    """
    user_prompt = f"""The student got this wrong:
Question: {question_text}
Student's answer: {student_answer}
Correct answer: {correct_answer}
Concept: {node_name} — {node_description}

Explain clearly. Return JSON only."""

    text, model, prompt = ask(EXPLAIN_PROMPT, user_prompt, temperature=0.5)
    return parse_ai_json(text), model, prompt
