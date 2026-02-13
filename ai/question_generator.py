"""Generate adaptive questions via Ollama at a specified difficulty."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json_dict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert tutor creating adaptive questions for a student.

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Step-by-step solution"
}

Rules:
1. Match the target difficulty level precisely.
   0.0 = absolute easiest version of this concept.
   0.5 = typical mid-level.
   1.0 = most challenging version.
2. NEVER repeat a question from the recent history provided.
3. ALWAYS generate the correct_answer field - do NOT include options.
4. Return ONLY the JSON, no other text.
5. For correct_answer, provide ONLY the final answer — not a sentence.
   Good: "42"  Bad: "The answer is 42"
6. CRITICAL: Every question MUST have exactly ONE clear correct answer.
   Never use multiple blanks (e.g. "__, __").
   Never ask for multiple values.
   For sequences, ask "What comes next?" (single answer).
7. Vary question formats: word problems, pure calculations, conceptual questions.
8. Never write "[shows X items]" or "[image of...]" — only real question text.
9. The question must end with a question mark, colon, period, or start with an imperative verb.
10. Keep the correct answer concise — under 200 characters.
11. Use LaTeX notation for math expressions: \\(\\sqrt{16}\\), \\(\\frac{1}{2}\\), \\(x^2\\).
12. NEVER describe visual elements in words — don't write "open circle at -3 and shading to the right" or "the number line shows". Write the mathematical expression instead.
13. Do NOT ask students to "graph", "draw", "sketch", or "plot" anything."""


def generate(node_name, node_description, topic_name, skill_description,
             target_difficulty_elo, question_type, recent_questions=None):
    """Generate a question via Ollama.

    Returns (question_dict, model_used, prompt_used).
    """
    # Map ELO difficulty to 0-1 scale for the prompt
    # ELO 400 = 0.0 (easiest), ELO 1200 = 1.0 (hardest)
    # Formula: (target - 400) / 800
    # At skill 800: target=559 → norm=0.20; at skill 1000: target=759 → norm=0.45
    norm_difficulty = max(0.0, min(1.0, (target_difficulty_elo - 400) / 800))

    recent_str = "\n".join(f"- {q}" for q in (recent_questions or [])[:20]) or "None"

    user_prompt = f"""Generate a {question_type} question for:
- Topic: {topic_name}
- Concept: {node_name}
- Concept description: {node_description}
- Difficulty: {norm_difficulty:.2f} (0.0=easiest, 1.0=hardest)
- Recent questions (DO NOT repeat these or ask similar ones):
{recent_str}

IMPORTANT: Do NOT include "options" in your response. Only provide question, correct_answer, and explanation.
The system will generate multiple choice options automatically.

Return JSON only."""

    text, model, prompt = ask(SYSTEM_PROMPT, user_prompt)
    logger.info('Raw LLM response for "%s": %s', node_name, text[:500])
    q_data = parse_ai_json_dict(text)

    logger.info('Generated %s question for "%s" at difficulty %.2f',
                question_type, node_name, norm_difficulty)
    return q_data, model, prompt
