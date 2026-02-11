**Mora: Specification for an Adaptive, LLM-Powered Learning Program**

Mora is a local, privacy-first adaptive learning system. It starts from any user-specified topic and dynamically generates questions using a local Ollama model. The system keeps the student in their "sweet spot" by targeting an 80% success rate per question, using an ELO-inspired rating system with Bayesian uncertainty decay. It follows a structured curriculum, adjusts progression based on performance, and heavily weights the most recent 30 questions when deciding the next one. All questions, attempts, and progress statistics are stored persistently in SQLite.

---

### Core Goals

- **Optimal Challenge Zone**: Target 80% correctness probability to maximize learning.
- **Adaptive Difficulty**: Increase difficulty after correct answers; decrease after incorrect ones.
- **Curriculum-Aware**: Follow a hierarchical structure of topics and curriculum nodes. Revisit prerequisites when struggling; advance when mastered.
- **Recent-History Driven**: The next question is primarily derived from analysis of the most recent 30 attempts (per-node accuracy, overall accuracy, improvement trend).
- **Local & Extensible**: Runs entirely offline with Ollama and SQLite.

---

### Architecture

- **Frontend**: Flask web application with Jinja2 templates and vanilla CSS/JS.
- **Backend**: Python 3.9+. Uses raw `sqlite3` (no ORM), `urllib.request` for Ollama HTTP calls, and `python-dotenv` for configuration. No pandas, no SQLAlchemy.
- **LLM Integration**: Ollama via its `/api/chat` HTTP endpoint. Model is configurable (default: `qwen3:8b`).
- **Storage**: Single SQLite file (`mora.db`).
- **Server**: Flask runs on `0.0.0.0:5002` in debug mode.

### Project Structure

The codebase follows a strict layered architecture. Each layer only depends on layers below it.

- **`config/settings.py`** — All configurable constants loaded from environment variables with defaults. Three config dictionaries: `ELO_DEFAULTS`, `DIFFICULTY_DEFAULTS`, `SESSION_DEFAULTS`.
- **`db/`** — Database connection helpers (`get_db`, `init_db`, `query_db`, `execute_db`) and the SQL schema file. All connections use `sqlite3.Row` for dict-like access and enable foreign keys.
- **`models/`** — One file per table. Raw SQL CRUD functions only. No business logic. Every function either calls `query_db` (for reads) or `execute_db` (for writes). Returns plain dicts.
- **`engine/`** — Pure functions with zero database or Flask dependencies. Contains the ELO algorithm, difficulty calibration, next-question selection logic, and answer matching.
- **`ai/`** — Ollama HTTP client, JSON response parser, and four prompt modules: curriculum generation, question generation, answer grading, and explanation generation.
- **`services/`** — Orchestration layer that combines models, engine, and AI modules. Three services: onboarding, question generation, and answer processing.
- **`routes/`** — Flask blueprints. Three blueprints: home (no prefix), session (`/session`), dashboard (`/dashboard`).
- **`templates/`** — Jinja2 HTML templates extending a shared `base.html`.
- **`static/`** — CSS stylesheet and session JavaScript (response timer, MCQ keyboard shortcuts).
- **`tests/`** — Unit tests using pytest with an `autouse` fixture that redirects `DB_PATH` to a temporary file for every test. No test ever touches `mora.db`.

### Configuration

All settings live in `config/settings.py` and are importable as module-level dictionaries.

**ELO_DEFAULTS**: initial_skill_rating is 1000.0, initial_uncertainty is 300.0, base_k_factor is 32.0, mastery_threshold is 0.75.

**DIFFICULTY_DEFAULTS**: target_success_rate is 0.80, recent_window is 30 attempts, elo_scale_factor is 400.0.

**SESSION_DEFAULTS**: target_success_rate is 0.80, max_generation_attempts is 2 (retry limit for Ollama calls). Sessions have no question limit — they continue indefinitely until the student clicks "End Session".

**Ollama**: base URL defaults to `http://localhost:11434`, model defaults to `qwen3:8b`. Both are overridable via `OLLAMA_BASE_URL` and `OLLAMA_MODEL` environment variables.

---

### Data Model

Seven tables stored in `mora.db`.

**students**: Stores student records. Fields: integer `id` (primary key), unique text `name`, datetime `created_at` with auto-timestamp.

**topics**: Stores learning topics. Fields: integer `id`, unique text `name`, optional text `description`, optional integer `parent_id` referencing another topic for hierarchical organization.

**curriculum_nodes**: Stores the ordered concepts within a topic. Fields: integer `id`, integer `topic_id` (foreign key to topics, required), text `name`, optional text `description`, integer `order_index` defaulting to 0 (determines curriculum sequence), text `prerequisites` defaulting to `'[]'` (a JSON array of node IDs that must be mastered first), real `mastery_threshold` defaulting to 0.75.

**sessions**: Tracks learning sessions. Fields: text `id` (UUID primary key), integer `student_id` (required foreign key), optional integer `topic_id`, datetime `started_at` with auto-timestamp, nullable datetime `ended_at`, integer `total_questions` and `total_correct` both defaulting to 0 (computed when session ends).

**questions**: Stores every generated question. Fields: integer `id`, integer `curriculum_node_id` (required foreign key), text `content` (the question text), text `question_type` constrained to 'mcq', 'short_answer', or 'problem', nullable text `options` (JSON array for MCQ choices), text `correct_answer`, nullable text `explanation` (LLM-generated step-by-step solution), nullable real `difficulty` (ELO-scale value), nullable real `estimated_p_correct`, nullable text `generated_prompt` (full prompt sent to Ollama for reproducibility), nullable text `model_used`, datetime `created_at`.

**attempts**: Records every student answer. Fields: integer `id`, integer `question_id` (required foreign key), integer `student_id` (required foreign key), text `session_id` (foreign key to sessions), nullable text `answer_given`, integer `is_correct` (0 or 1), nullable real `partial_score` (0 to 1 for open-ended), nullable real `response_time_seconds`, datetime `timestamp` with auto-timestamp.

**student_skill**: Tracks ELO skill state per student per curriculum node. Fields: integer `id`, integer `student_id` (required), integer `curriculum_node_id` (required), real `skill_rating` defaulting to 1000.0, real `uncertainty` defaulting to 300.0, real `mastery_level` defaulting to 0.0, integer `total_attempts` defaulting to 0, integer `correct_attempts` defaulting to 0, datetime `last_updated`. Has a unique constraint on (student_id, curriculum_node_id). Uses `INSERT ... ON CONFLICT DO UPDATE` for upsert operations.

**Indexes**: On `attempts.timestamp`, `attempts.student_id`, `attempts.session_id`, `student_skill.student_id`, and `curriculum_nodes.topic_id`.

---

### Models Layer

Each model file provides simple CRUD functions. Key behaviors:

- **`student_skill.get(student_id, node_id)`**: Returns the existing row if found, otherwise returns a default dictionary with initial values (rating 1000, uncertainty 300, mastery 0, zero attempts). This means the engine can always work with skill data even before a student_skill row exists.
- **`attempt.get_recent(student_id, limit=30)`**: Joins attempts with questions to return enriched rows including the question content, correct answer, difficulty, curriculum_node_id, and question_type. Ordered by timestamp descending.
- **`session.create(student_id, topic_id)`**: Generates a UUID string as the session ID.
- **`session.end_session(session_id)`**: Counts total attempts and correct attempts from the attempts table for that session, writes the totals, and sets `ended_at` to the current timestamp.

---

### Adaptive Algorithm

#### ELO Skill Model

Each student has a separate skill record per curriculum node, consisting of a skill_rating (ELO-scale, starting at 1000) and an uncertainty value (starting at 300).

**Probability of correct answer**: `P(correct) = 1 / (1 + 10^((D - S) / 400))` where S is skill_rating and D is question difficulty, both on the ELO scale. When S equals D, the probability is exactly 0.5.

**Target difficulty for 80% success**: Solve the probability formula for D given P = 0.8: `D = S + 400 * log10(1/0.8 - 1)`, which simplifies to approximately S minus 241. This means questions are targeted about 241 ELO points below the student's skill level.

**K-factor**: Dynamic, calculated as `base_K * (uncertainty / initial_uncertainty)`. At the initial uncertainty of 300, K equals the base of 32. As uncertainty decreases, K shrinks, making the rating more stable.

**Skill update after each attempt**: Compute the expected probability of a correct answer using the actual question difficulty. The actual outcome is 1.0 for correct or 0.0 for wrong. The rating change is `delta = K * (actual - expected)`. The new rating is the old rating plus delta. Uncertainty decays by multiplying by 0.95 after each attempt, with a floor of 50.

**Mastery computation**: `mastery_level = 0.6 * normalized_rating + 0.4 * recent_accuracy`. The normalized rating maps the 400-1600 ELO range to 0-1, clamped at both ends. Recent accuracy is computed from the last 30 attempts on that specific node, including the current attempt.

**Mastery threshold**: A node is considered mastered when mastery_level reaches 0.75.

#### Difficulty Calibration

After computing the base target difficulty from the ELO formula, the system applies a calibration adjustment based on the student's recent accuracy on that specific node. If fewer than 3 attempts exist for the node, no adjustment is made. Otherwise: compute the error as `recent_accuracy - 0.80`, then adjust target difficulty by `error * 100`. This means if the student is hitting 90% (10% above target), the difficulty increases by 10 ELO points; if hitting 60% (20% below), it decreases by 20 points.

#### Next Question Selection

The system analyzes the most recent 30 attempts (across all nodes) and applies a priority-ordered decision process:

1. **Analyze recent history**: Compute overall accuracy, per-node accuracy, per-node result lists, and an improvement trend. The trend compares the first half of attempts to the second half — if the second half's accuracy exceeds the first half's by more than 10 percentage points, the trend is "improving"; if the reverse, "declining"; otherwise "stable". Requires at least 6 attempts (3 per half) for trend detection.

2. **Focus node selection** (checked in order, first match wins):
   - If a current node exists and its recent accuracy is between 60% and 90% and it is not mastered: stay on the current node.
   - If a current node exists and its recent accuracy is below 60%: fall back to the first unmastered prerequisite of that node.
   - If a current node exists and it is mastered or accuracy exceeds 90%: advance to the next unmastered node in curriculum order.
   - Otherwise, pick the weakest recently-practiced node (lowest accuracy among unmastered nodes with recent attempts).
   - If no recently-practiced unmastered nodes exist, pick the next untouched node in curriculum order (zero attempts).
   - As a final fallback, pick the node with the lowest mastery_level among all nodes.

3. **Compute question parameters**: Calculate target difficulty using the ELO formula plus calibration. Determine question type based on mastery: below 0.3 mastery produces MCQ, 0.3 to 0.6 produces short_answer, above 0.6 produces problem type.

---

### Answer Grading

Three-tier grading system:

**MCQ and short_answer**: Graded locally without Ollama. The answer matching normalizes both strings (lowercase, strip whitespace and non-alphanumeric characters). For MCQ, it extracts the letter (A-D) from both student and correct answers and compares letters. For short_answer, it tries exact string match, then numeric equivalence (parses both as floats and compares with tolerance of 1e-9), then a containment check (if one string contains the other and their length ratio exceeds 0.8, it counts as correct). If none match, it computes a character overlap ratio — if above 70%, the answer is marked as "close" (not correct, but close). Returns a tuple of (is_correct, is_close).

**Problem type**: Sent to Ollama for LLM-based grading. The grading prompt asks the model to compare the student answer to the correct answer and return JSON with is_correct (boolean), partial_score (0 to 1), and feedback (text). Uses temperature 0.3 for consistency. If the Ollama call fails, falls back to the local exact-match grading.

---

### LLM Integration

All Ollama communication goes through a single HTTP client that sends chat completion requests to the `/api/chat` endpoint with streaming disabled. Every call returns a tuple of (response_text, model_used, full_prompt) for logging and reproducibility. The timeout is 120 seconds.

**JSON parsing**: All AI responses are expected to be JSON. The parser tries raw JSON first, then extracts from markdown code blocks (triple backticks with or without the `json` language tag), then searches for the first JSON object or array pattern in the text. Raises an error if no valid JSON is found.

#### Curriculum Generation

When a student enters a topic that doesn't exist yet, the system generates a curriculum by sending a structured prompt to Ollama asking for 8-12 ordered learning nodes. The prompt specifies: nodes should go from fundamental to advanced, prerequisites reference node names (not indices), early nodes should have no prerequisites, each node should be focused and testable, and descriptions should be detailed enough to generate questions from. Temperature is 0.7. After parsing, prerequisite names are resolved to indices and then to database IDs when the nodes are created.

#### Local Generators

Some curriculum nodes are handled locally without calling the LLM. The system detects these by keyword matching on the node name and description.

**Clock reading**: When a node's name or description contains clock-related keywords ("clock", "telling time", "analog time", etc.), an SVG analog clock face is generated locally. The clock has 12 hour numbers, tick marks, and correctly positioned hour and minute hands. The hour hand accounts for fractional position from minutes. The question is always MCQ with 4 time choices. Two modes: hour-only (minute always 0) if the node mentions "hour" without "half" or "quarter", otherwise quarter-hour mode with minutes from {0, 15, 30, 45}. Dedup avoids recently asked times. No LLM call needed.

#### Question Generation

For nodes not handled by local generators, the system calls the LLM. The ELO-scale difficulty is normalized to a 0-1 scale for the prompt: difficulty of 600 maps to 0.0 (easiest), 1400 maps to 1.0 (hardest). The prompt includes the topic name, concept name and description, normalized difficulty, question type (mcq/short_answer/problem), and a combined exclude list of all session questions and all lifetime correctly-answered questions. The system prompt has 14 rules covering: difficulty matching, dedup, MCQ format (exactly 4 options, correct answer among them), answer format (concise, not a sentence), single correct answer (no multiple blanks), no placeholder text, no "all/none of the above", punctuation, and answer length limits. If generation fails, it retries up to 2 times total.

#### Question Validation

Every generated question passes through a 12-rule post-generation validator before being accepted. If validation fails, the system retries generation. Rules:
1. Question text minimum 10 characters.
2. Answer not empty or placeholder (rejects empty strings, "?", "...", "N/A", "none", "null").
3. Choices must be unique after stripping letter prefixes (A/B/C/D) — case-insensitive.
4. Correct answer must appear among choices (by text match, letter match, or index).
5. Answer not given away in question text, with exceptions for math expressions ("What is 86 - 43?" answer "43" is allowed), comparison questions, classification questions, and "what/which" identification questions.
6. No placeholder text patterns ("[shows", "[image", "[picture", "[display", "[insert").
7. Answer maximum 200 characters.
8. No HTML or markdown artifacts ("</", "```").
9. Minimum 3 choices if any are provided.
10. Answer length bias prevention — rejects if correct answer is 3x longer than average distractor AND 15+ chars longer than the longest distractor.
11. No "all of the above", "none of the above", "none of these", or similar banned choices.
12. Question must end with punctuation (? : .), contain a blank (__), or start with an imperative verb (solve, calculate, find, etc.).

#### Question Deduplication

Three dedup layers prevent question repetition:
1. **Session dedup**: Never repeat any question within the same session. All question texts from the current session are collected and any generated question matching one is rejected.
2. **Global correct-answer dedup**: Never repeat a question the student has correctly answered in any previous session. A lifetime set of all correctly-answered question texts is queried from the attempts table and used as an exclusion set.
3. **LLM prompt dedup**: The combined exclusion set (session + global correct) is passed to the LLM in the prompt with an instruction not to repeat or ask similar questions.

Both dedup checks happen post-generation as hard rejections. If a generated question matches either set, it is discarded and the system retries.

#### Explanation Generation

When a student answers incorrectly, the feedback page calls the explainer to generate a structured explanation. The prompt receives the question, correct answer, student's wrong answer, and the concept name. It returns JSON with four fields: encouragement (brief positive message), explanation (step-by-step correct solution), key_concept (the core idea to understand), and tip (practical advice for similar questions). Temperature is 0.5. If the Ollama call fails, the system falls back to a static message showing the correct answer with "Keep going!" as encouragement.

---

### User Flow

#### Home Page (GET /)

Displays a form with two fields: student name and topic name. Below the form, shows a list of existing students as clickable chips that link to their topic picker page. Also shows existing topics as non-clickable chips.

#### Onboarding (POST /onboard)

Receives student_name and topic_name from the form. Gets or creates the student by name. If the topic doesn't exist, calls Ollama to generate a curriculum (8-12 nodes), creates the topic in the database, and creates all curriculum nodes with resolved prerequisite IDs. Redirects to the topic picker page for that student.

#### Topic Picker (GET /pick-topic/<student_id>)

Shows the student's name and lists all available topics as buttons. Each button is a form that submits to start a session with that student and topic. Also includes a form to create a new topic (which goes through onboarding again).

#### Session Start (POST /session/start)

Receives student_id and topic_id. Creates a new session record with a UUID. Calls the question generation pipeline to produce the first question and stores it in the Flask session. Redirects to the question page.

#### Question Page (GET /session/<session_id>/question)

Uses a two-panel layout. A top bar shows the student name, topic mastery percentage with a progress bar, running session stats (correct/total with accuracy), and an "End Session" button.

**Left panel**: The current question. Shows the curriculum node name as a badge, the question type as a badge, and the question text. For clock-reading nodes, an SVG analog clock face is displayed above the question. For MCQ, renders four clickable choice buttons with letter indicators (A/B/C/D) and the choice text (with any LLM-generated letter prefix stripped via a custom Jinja2 filter). For short_answer and problem types, renders a textarea with a submit button. A hidden field tracks response time via JavaScript. MCQ buttons support A/B/C/D keyboard shortcuts. At the bottom of the question card, a difficulty indicator shows: 10 dots (filled proportionally), a numeric score (1-10), and the estimated probability of the student getting it correct. The difficulty score maps ELO difficulty to a 1-10 scale: ELO 600 = 1, ELO 1400 = 10. The probability is computed from the ELO formula P(correct) = 1/(1+10^((D-S)/400)) and should hover around 80% when the adaptive system is calibrated.

**Right panel**: Two cards stacked vertically. The top card shows the result of the previous question — a green "Correct!" or red "Wrong" banner with the previous question text, the student's answer, and (if wrong) the correct answer, plus the skill name and ELO rating. On the first question of a session, this shows a placeholder message. The bottom card shows "Topic Progress" — a scrollable list of all curriculum nodes with their name, mastery percentage, and a mastery progress bar. Mastered nodes are highlighted in green text. For MCQ, renders four clickable choice buttons with letter indicators (A/B/C/D) and the choice text (with any LLM-generated letter prefix stripped via a custom Jinja2 filter). For short_answer and problem types, renders a textarea with a submit button. A hidden field tracks response time via JavaScript (timer starts on page load, captured on submit). MCQ buttons support keyboard shortcuts (pressing A/B/C/D keys). An "End Session Early" button links to the session end page.

#### Answer Submission (POST /session/<session_id>/answer)

Receives the student's answer text and response time. Calls the answer service which grades the answer, updates ELO, and records the attempt. If the answer is correct: stores the result in Flask session, generates the next question, and redirects to the question page. If wrong: stores the result and redirects to the feedback page.

#### Feedback Page (GET /session/<session_id>/feedback)

Shown only after wrong answers. Displays the topic mastery bar at the top (same as the question page). Calls the Ollama explainer to generate an explanation. Displays: a "Not quite!" header, the LLM-generated encouragement, the student's answer (in red) vs the correct answer (in green), the LLM-generated step-by-step explanation in a yellow box, the key concept with a left-border accent, a tip with a left-border accent, the current skill name/rating/mastery percentage, and a "Next Question" button that submits a POST to generate the next question.

#### Session End (GET /session/<session_id>/end)

Finalizes the session by computing totals from the attempts table and writing them to the session record. Displays: a "Session Complete!" header, three stat cards (total questions, correct count, accuracy percentage with color coding: green above 80%, amber above 60%, red below), a skills-practiced list showing each node's name with a mastery progress bar, ELO rating, and a "Mastered!" badge if applicable, and action buttons to continue learning or view the dashboard.

#### Dashboard Index (GET /dashboard/)

Lists all students as cards, each showing total attempts, mastered node count, and in-progress node count. Each card links to that student's overview.

#### Student Overview (GET /dashboard/<student_id>)

Shows the student's full progress. For each topic, displays a grid of curriculum node cards. Each card is color-coded: green background for mastered nodes, purple background for in-progress nodes, gray for untouched nodes. Each card shows the node name, a mastery progress bar, mastery percentage, ELO rating, and attempt count. Below the node grid, a table shows recent sessions with date, question count, correct count, and accuracy. Links to the full history page and back to the topic picker.

#### Attempt History (GET /dashboard/<student_id>/history)

Paginated table of all attempts (30 per page) showing timestamp, concept name, question text (truncated to 60 characters), the student's answer, and whether it was correct. Correct rows have a green background; wrong rows have a light red background. Includes previous/next pagination links.

---

### Frontend Details

**CSS**: Uses CSS custom properties for theming. Primary color is indigo (#4f46e5). Card-based layout with 12px border radius. MCQ choices are rendered as full-width buttons in a vertical grid with circular letter indicators. Progress bars use the primary color, mastery bars use green when mastered. The design is responsive with a max-width of 800px.

**JavaScript**: A single `session.js` file loaded on the question page. It starts a timer on page load and captures elapsed seconds into a hidden form field on submit. Adds keyboard event listeners for A/B/C/D keys that click the corresponding MCQ button. Auto-focuses the text input for non-MCQ questions.

**Template filter**: The Flask app registers a custom Jinja2 filter called `strip_letter` that removes leading letter prefixes (like "A) " or "B. ") from MCQ option text, since the LLM sometimes includes them and the template already adds its own letter indicators.

---

### Testing

All tests use pytest. A shared `conftest.py` fixture (`temp_db`) is marked `autouse` and redirects `DB_PATH` to a temporary file for every test, then runs `init_db()` to create the schema. No test touches the production database.

Test files cover: ELO algorithm (probability, target difficulty, skill updates, K-factor, mastery computation), difficulty calibration, answer matching (exact, case-insensitive, numeric, MCQ letter extraction), next-question selection (empty history, per-node accuracy, node advancement on mastery), JSON parsing (raw, markdown-wrapped, surrounding text, invalid input), question validation (all 12 rules with positive and negative cases including edge cases for math expressions, letter-prefixed choices, length bias, and banned choice patterns), and model CRUD operations (student creation, topic creation, curriculum nodes, sessions, skill upsert, attempts, session finalization).
