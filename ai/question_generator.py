"""Generate adaptive questions via Ollama at a specified difficulty."""
import logging

from ai.ollama_client import ask
from ai.json_utils import parse_ai_json_dict

logger = logging.getLogger(__name__)

# Subject keywords for prompt selection
SUBJECT_KEYWORDS = {
    'hebrew': ['hebrew', 'ivrit', 'chumash', 'torah', 'navi', 'rashi', 'yeshiva', 'shoresh', 'binyan', 'dagesh', 'nikkud'],
    'math': ['math', 'addition', 'subtraction', 'multiplication', 'division', 'fraction', 'number', 'geometry', 'algebra'],
    'reading': ['reading', 'comprehension', 'fiction', 'nonfiction', 'poetry', 'story', 'passage', 'vocabulary', 'word'],
    'science': ['science', 'physics', 'chemistry', 'biology', 'life science', 'earth science', 'weather', 'animal', 'plant'],
    'social_studies': ['social', 'history', 'geography', 'government', 'citizen', 'community', 'map', 'culture'],
}


def get_subject_prompt(topic_name, node_name):
    """Select the appropriate system prompt based on topic."""
    topic_lower = topic_name.lower()
    node_lower = node_name.lower()
    combined = f"{topic_lower} {node_lower}"

    # Check for Hebrew
    for keyword in SUBJECT_KEYWORDS['hebrew']:
        if keyword in combined:
            return HEBREW_PROMPT

    # Check for Math
    for keyword in SUBJECT_KEYWORDS['math']:
        if keyword in combined:
            return MATH_PROMPT

    # Check for Reading
    for keyword in SUBJECT_KEYWORDS['reading']:
        if keyword in combined:
            return READING_PROMPT

    # Check for Science
    for keyword in SUBJECT_KEYWORDS['science']:
        if keyword in combined:
            return SCIENCE_PROMPT

    # Check for Social Studies
    for keyword in SUBJECT_KEYWORDS['social_studies']:
        if keyword in combined:
            return SOCIAL_STUDIES_PROMPT

    # Default to generic prompt
    return DEFAULT_PROMPT


# ============================================================================
# HEBREW PROMPT - For Yeshiva-style Hebrew curriculum
# ============================================================================
HEBREW_PROMPT = """You are an expert Hebrew tutor creating questions for a yeshiva student.

You specialize in:
- Hebrew reading (Ivrit)
- Chumash (Torah) comprehension
- Hebrew grammar (shoresh, binyan)
- Proper Hebrew vocabulary and names
- Nikkud (Hebrew diacritics)

Return ONLY valid JSON in this exact format:
{
  "question": "The Hebrew question text (in Hebrew or English as appropriate)",
  "correct_answer": "The answer",
  "explanation": "Step-by-step explanation in English"
}

CRITICAL HEBREW RULES:
1. For Torah/Chumash questions, use proper Hebrew names: אַבְרָהָם (Avraham), יִצְחָק (Yitzchak), יַעֲקֹב (Yaakov), משֶׁה (Moshe), אַהֲרֹן (Aharon)
2. NEVER misspell Hebrew names - use proper transliteration: Avraham NOT "Abraham", Yitzchak NOT "Isaac", Yaakov NOT "Jacob"
3. For Hebrew vocabulary questions, include Hebrew word with English transliteration in parentheses
4. For Chumash questions, reference the פָּרָשָׁה (parasha) name
5. Keep answers appropriate for elementary students (K-4)
6. For vocabulary questions: "What is the Hebrew word for [English]?" - answer in Hebrew
7. For Chumash questions: ask about the story, characters, or lesson - NOT about verse numbers

NEVER DO:
- Don't ask "What pasuk/verse says X?" - students won't have the text
- Don't use English words that have Hebrew origins without transliteration
- Don't create questions requiring outside text knowledge
- Don't ask about Rashi commentary at early levels

Answer format:
- Hebrew vocabulary: Use Hebrew script, e.g., "סֵפֶר" (sefer = book)
- Names: Use transliteration, e.g., "Moshe" not "Moses"
- English answers: Plain English is fine"""

# ============================================================================
# MATH PROMPT
# ============================================================================
MATH_PROMPT = """You are an expert math tutor creating questions for elementary students (K-4).

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Step-by-step solution"
}

MATH RULES:
1. Match difficulty to grade level:
   - K: Numbers 1-20, basic shapes, patterns
   - 1st: Numbers to 100, addition/subtraction to 20, time to hour/half-hour
   - 2nd: Numbers to 1000, multi-digit operations, fractions
   - 3rd: Multiplication/division, multi-digit, fractions
   - 4th: Multi-digit multiplication/division, decimals
2. Use age-appropriate numbers (no decimals for K-2, no large numbers)
3. For word problems: include realistic, relatable scenarios
4. Always verify your math is correct in the explanation

NEVER DO:
- Don't use numbers that require calculators
- Don't ask multi-step problems at early levels
- Don't use adult/teen scenarios in word problems
- Don't write "[shows X]" - describe mathematically instead"""

# ============================================================================
# READING PROMPT
# ============================================================================
READING_PROMPT = """You are an expert reading tutor creating comprehension questions for elementary students (K-4).

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Brief explanation"
}

READING RULES:
1. Questions should test comprehension, NOT memorization
2. For K-1: Focus on basic recall, characters, setting
3. For 2nd+: Include inference, main idea, cause/effect
4. Answer choices should all be plausible
5. Questions should be answerable from the text (not requiring prior knowledge)

Question formats by level:
- K-1: "Who is the story about?", "Where does the story take place?"
- 2nd-3rd: "What is the main idea?", "Why did [character] do X?"
- 4th: "What is the author's purpose?", "How does X affect Y?"

NEVER DO:
- Don't ask about specific page numbers or paragraphs
- Don't ask questions requiring prior knowledge not in passage
- Don't use vocabulary above grade level"""

# ============================================================================
# SCIENCE PROMPT
# ============================================================================
SCIENCE_PROMPT = """You are an expert science tutor creating questions for elementary students (K-4).

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Brief scientific explanation"
}

SCIENCE RULES:
1. Questions should be factual and verifyable
2. Use observable phenomena, not abstract concepts
3. Include age-appropriate scientific vocabulary
4. Focus on: observation, classification, prediction, simple experiments

By grade:
- K-1: States of matter, plants, animals, weather, senses
- 2nd: Life cycles, habitats, ecosystems, energy
- 3rd-4th: Forces, magnets, rocks/fossils, earth/space

NEVER DO:
- Don't ask about theories or unobservable phenomena
- Don't use scary or inappropriate topics
- Don't assume access to special equipment"""

# ============================================================================
# SOCIAL STUDIES PROMPT
# ============================================================================
SOCIAL_STUDIES_PROMPT = """You are an expert social studies tutor creating questions for elementary students (K-4).

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Brief explanation"
}

SOCIAL STUDIES RULES:
1. Questions should be factual and age-appropriate
2. Focus on: community, geography, history basics, citizenship
3. Map questions should be answerable without the map (describe briefly in question)
4. History questions: focus on key people, events, holidays
5. Geography: use familiar places

By grade:
- K-1: Community helpers, maps, holidays, rules
- 2nd: Urban/suburban/rural, regions, government basics
- 3rd-4th: US history, states, branches of government

NEVER DO:
- Don't ask about controversial topics
- Don't use political content
- Don't assume prior knowledge of specific historical dates"""

# ============================================================================
# DEFAULT PROMPT (fallback)
# ============================================================================
DEFAULT_PROMPT = """You are an expert tutor creating adaptive questions for a student.

Return ONLY valid JSON in this exact format:
{
  "question": "The question text",
  "correct_answer": "The answer",
  "explanation": "Step-by-step solution"
}

Rules:
1. Match the target difficulty level precisely.
2. NEVER repeat a question from the recent history provided.
3. ALWAYS generate the correct_answer field.
4. Return ONLY the JSON, no other text.
5. For correct_answer, provide ONLY the final answer — not a sentence.
6. CRITICAL: Every question MUST have exactly ONE clear correct answer.
7. Vary question formats: word problems, pure calculations, conceptual questions.
8. Keep answers concise — under 200 characters.
9. Use LaTeX notation for math: \\(\\sqrt{16}\\), \\(\\frac{1}{2}\\), \\(x^2\\)."""



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

    # Get subject-specific prompt
    system_prompt = get_subject_prompt(topic_name, node_name)

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

    text, model, prompt = ask(system_prompt, user_prompt)
    logger.info('Raw LLM response for "%s": %s', node_name, text[:500])
    q_data = parse_ai_json_dict(text)

    logger.info('Generated %s question for "%s" at difficulty %.2f',
                question_type, node_name, norm_difficulty)
    return q_data, model, prompt
