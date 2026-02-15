"""Generate adaptive questions via Ollama at a specified difficulty.

One universal prompt with subject-specific rules injected.
LLM always provides complete MCQ options — no algorithmic distractors.
"""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json_dict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert tutor creating questions for elementary students (K-4).

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "options": ["option_a", "option_b", "option_c", "option_d"],
  "explanation": "Step-by-step explanation"
}

CRITICAL RULES:
1. Include exactly 4 options. One MUST be the exact correct_answer text. The other 3 must be plausible but wrong.
2. All 4 options must be the SAME TYPE (all numbers, all words, all phrases).
3. Options must be unique — no duplicates.
4. The correct_answer value must appear verbatim as one of the 4 options.
5. Keep answers concise — under 100 characters.
6. Every question MUST have exactly ONE clear correct answer.
7. NEVER repeat a question from the recent history provided.
8. NEVER reference images, pictures, diagrams, graphs, or visual aids.
9. Verify your math is correct before responding.
10. Return ONLY the JSON, no other text."""

# Subject-specific rules injected into user prompt
SUBJECT_RULES = {
    'hebrew': """HEBREW RULES:
- For Torah/Chumash: use proper Hebrew names (Avraham, Yitzchak, Yaakov, Moshe, Aharon)
- Use proper transliteration: Avraham NOT "Abraham", Yitzchak NOT "Isaac"
- For vocabulary: include Hebrew with transliteration, e.g. sefer (book)
- All 4 options must be same type: all Hebrew, all transliterations, or all English
- Don't ask about specific verses or Rashi at early levels
- Keep appropriate for elementary students""",

    'math': """MATH RULES:
- K: Numbers 1-20, basic shapes, patterns
- 1st: Numbers to 100, addition/subtraction to 20, time to hour/half-hour
- 2nd: Numbers to 1000, multi-digit operations, fractions intro
- 3rd: Multiplication/division, multi-digit, fractions
- 4th: Multi-digit multiplication/division, decimals
- Use age-appropriate numbers, no calculators needed
- For word problems: realistic kid-friendly scenarios
- VERIFY your arithmetic is correct in the explanation""",

    'reading': """READING RULES:
- K-1: Basic recall, characters, setting
- 2nd+: Inference, main idea, cause/effect
- Questions should be answerable without prior knowledge
- Don't reference specific pages or paragraphs""",

    'science': """SCIENCE RULES:
- K-1: States of matter, plants, animals, weather, senses
- 2nd: Life cycles, habitats, ecosystems
- 3rd-4th: Forces, magnets, rocks, earth/space
- Use observable phenomena, not abstract concepts""",

    'social_studies': """SOCIAL STUDIES RULES:
- K-1: Community helpers, maps, holidays, rules
- 2nd: Urban/suburban/rural, regions, government basics
- 3rd-4th: US history, states, branches of government
- Focus on key people, events, holidays""",
}

SUBJECT_KEYWORDS = {
    'hebrew': ['hebrew', 'ivrit', 'chumash', 'torah', 'navi', 'rashi',
               'yeshiva', 'shoresh', 'binyan', 'dagesh', 'nikkud'],
    'math': ['math', 'addition', 'subtraction', 'multiplication', 'division',
             'fraction', 'number', 'geometry', 'algebra'],
    'reading': ['reading', 'comprehension', 'fiction', 'nonfiction', 'poetry',
                'story', 'passage', 'vocabulary', 'word'],
    'science': ['science', 'physics', 'chemistry', 'biology', 'life science',
                'earth science', 'weather', 'animal', 'plant'],
    'social_studies': ['social', 'history', 'geography', 'government',
                       'citizen', 'community', 'map', 'culture'],
}


def _detect_subject(topic_name, node_name):
    """Detect subject from topic and node names."""
    combined = f"{topic_name} {node_name}".lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return subject
    return None


def generate(node_name, node_description, topic_name, skill_description,
             target_difficulty_elo, question_type, recent_questions=None):
    """Generate a question via Ollama.

    Returns (question_dict, model_used, prompt_used).
    """
    # Map ELO difficulty to human-readable label
    norm_difficulty = max(0.0, min(1.0, (target_difficulty_elo - 400) / 800))
    if norm_difficulty < 0.3:
        difficulty_label = "easy"
    elif norm_difficulty < 0.6:
        difficulty_label = "medium"
    else:
        difficulty_label = "hard"

    recent_str = "\n".join(f"- {q}" for q in (recent_questions or [])[:20]) or "None"

    subject = _detect_subject(topic_name, node_name)
    subject_rules = SUBJECT_RULES.get(subject, '')

    if question_type == 'mcq':
        format_instruction = (
            "Include exactly 4 \"options\" in your response. "
            "One option MUST be the exact correct_answer text. "
            "The other 3 must be plausible but wrong."
        )
    else:
        format_instruction = (
            "Do NOT include \"options\" — this is a short-answer question. "
            "Only provide question, correct_answer, and explanation."
        )

    user_prompt = f"""Generate a {question_type} question:
- Topic: {topic_name}
- Concept: {node_name}
- Description: {node_description}
- Difficulty: {difficulty_label} ({norm_difficulty:.2f})
- Recent questions (DO NOT repeat or ask similar):
{recent_str}

{format_instruction}

{subject_rules}

Return JSON only."""

    text, model, prompt = ask(SYSTEM_PROMPT, user_prompt)
    logger.info('Raw LLM response for "%s": %s', node_name, text[:500])
    q_data = parse_ai_json_dict(text)

    logger.info('Generated %s question for "%s" at difficulty %s',
                question_type, node_name, difficulty_label)
    return q_data, model, prompt
