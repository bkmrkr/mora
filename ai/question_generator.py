"""Generate adaptive questions via Ollama at a specified difficulty."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert tutor creating adaptive questions for a student.

Return ONLY valid JSON:
{
  "question": "The question text",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct_answer": "The answer",
  "explanation": "Step-by-step solution",
  "estimated_difficulty": 0.65,
  "tags": ["concept1", "concept2"]
}

Rules:
1. Match the target difficulty level precisely.
2. Never repeat a question from the recent history.
3. For MCQ: exactly 4 options, correct answer must be one of the option letters (A, B, C, or D).
4. For short_answer: correct_answer should be a concise string. Omit the options field.
5. For problem: include multi-step problems with worked solutions in explanation. Omit options.
6. Return ONLY the JSON, no other text."""


def generate(node_name, node_description, topic_name, skill_description,
             target_difficulty_elo, question_type, recent_questions=None):
    """Generate a question via Ollama.

    Returns (question_dict, model_used, prompt_used).
    """
    # Map ELO difficulty to 0-1 scale for the prompt
    norm_difficulty = max(0.0, min(1.0, (target_difficulty_elo - 600) / 800))

    recent_str = "\n".join(f"- {q}" for q in (recent_questions or [])) or "None"

    user_prompt = f"""Generate a {question_type} question for:
- Topic: {topic_name}
- Concept: {node_name}
- Concept description: {node_description}
- Difficulty: {norm_difficulty:.2f} (0.0=easiest, 1.0=hardest)
- Recent questions (DO NOT repeat):
{recent_str}

Return JSON only."""

    text, model, prompt = ask(SYSTEM_PROMPT, user_prompt)
    q_data = parse_ai_json(text)

    logger.info('Generated %s question for "%s" at difficulty %.2f',
                question_type, node_name, norm_difficulty)
    return q_data, model, prompt
