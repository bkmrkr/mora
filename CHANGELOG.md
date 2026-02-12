# Mora Changelog

## [Unreleased]

### Fixed
- **Difficulty always near zero**: Questions were too easy because normalization used wrong ELO range (500-1100 instead of 400-1200). Changed formula from `(diff-500)/600` to `(diff-400)/800`. Now skill=800 gives norm=0.20, skill=1000 gives norm=0.45
- **ELO config drift**: Initial uncertainty was 500 (spec says 350), base K was 64 (spec says 32), schema default was 500 (spec says 350). All corrected to match spec — skill updates now faster and more accurate

### Changed
- Difficulty normalization now consistent across: LLM prompt, question display, and session route

## [2026-02-12]

### Added
- **Server-side math rendering**: LaTeX expressions rendered to SVG images server-side via matplotlib's mathtext (Computer Modern font, textbook look). Replaces KaTeX CDN — works offline, no flash of raw LaTeX, no internet required. Applied to question text, MCQ options, answers, explanations, and feedback via `| render_math` Jinja filter. LRU-cached (512 expressions), thread-safe
- **KaTeX math rendering** (replaced): ~~LaTeX expressions from LLM rendered via KaTeX CDN auto-render~~ — superseded by server-side matplotlib rendering above
- **Inequality number line SVG generator**: Local generator (no LLM) for "Solving Inequalities" nodes — shows actual number line diagrams with open/filled circles and colored solution regions instead of text descriptions. MCQ options are inequality expressions (x > -3), not visual descriptions
- Validator Rules 16-17: reject text descriptions of visual diagrams ("open circle at", "shading to the right") and draw/graph/sketch imperatives — forces LLM to produce mathematical expressions
- LLM prompt rules 15-17: use LaTeX notation, never describe visuals in text, don't ask students to graph/draw
- 17 new tests for math renderer: expression rendering, delimiter handling, cache, thread safety, fallback (491 total)
- 22 new tests for inequality generator, validator Rules 16-17, and Rule 5 letter prefix regression

### Fixed
- **Rule 5 letter prefix bypass (Q#421)**: "Solve the inequality: x > -3" with answer "C) x > -3" passed Rule 5 because the letter prefix "C) " prevented the substring match. Now strips MCQ letter prefix before checking if answer text appears in question
- **LaTeX escape crash**: LLM returns `\(\sqrt{16} \times \sqrt{9}\)` inside JSON — `\(`, `\s`, `\t` are invalid JSON escapes. Added `_fix_latex_escapes()` that double-escapes non-structural backslashes as fallback after raw parse fails
- Request/response logging to `mora_debug.log` with daily rotation (3-day retention) — every click, form submission, and exception with full traceback
- `parse_ai_json_dict()` error messages now include the raw LLM text for debugging
- **Difficulty normalization bug (root cause of easy questions)**: The ELO difficulty was being normalized incorrectly. Formula `(target - 500) / 600` mapped skill 800 to difficulty 0.10 (nearly easiest). Changed to `(target - 400) / 800` which maps skill 800 → 0.20, skill 1000 → 0.45. Questions will now scale properly from easy to hard. Updated in question_generator.py and routes/session.py
- **Initial uncertainty in schema**: Changed default from 500 to 350 to match spec. Updated schema.sql and test

## [2026-02-11]

### Fixed
- **Server crash on session start**: `AttributeError: 'list' object has no attribute 'get'` — `parse_ai_json()` returned a JSON array from LLM but all callers assumed dict. Added `parse_ai_json_dict()` that enforces dict return, extracts first dict from arrays. Updated question_generator, answer_grader, and explainer.
- **Answer normalization destroys fractions/percentages**: `_normalize()` regex `[^\w\s\d.-]` stripped `/`, `%`, `$` — caused "3/4" → "34" (false match), "50%" → "50". Fixed regex to preserve these characters.
- **Validator crash on non-string LLM values**: LLM returning int as `correct_answer` or string as `options` crashed the validator. Added `str()` wrapping and list type guard.
- **Missing node_description in feedback**: `explain()` call received empty string instead of node context. Propagated `node_description` through full pipeline (question_service → _load_question_from_db → answer_service → feedback route).

### Added
- `parse_ai_json_dict()` in `ai/json_utils.py` — type-safe JSON parsing guaranteeing dict return
- Type guard in `question_service.py` — rejects non-dict generator results and retries
- `scripts/validate_questions.py` — deterministic DB question validation against all 15 rules (no LLM calls), reports pass/fail grouped by rule
- 82 new tests (447 total): json_utils_dict (12), answer_matching edge cases (14), answer_service integration (14), question_service with mocked generator (9), local clock generators (14), answer_grader mock (8), explainer mock (6), validator type safety (5)

### Added
- Research paper (paper.md) situating Mora's design within educational research literature, identifying established foundations vs. novel contributions
- Initial project structure: config, db, models, engine, ai, services, routes
- SQLite schema with 7 tables: students, topics, curriculum_nodes, sessions, questions, attempts, student_skill
- Database layer (get_db, init_db, query_db, execute_db)
- Configuration with ELO defaults, Ollama settings, session defaults
- Question validator with 12 rules ported from kidtutor (min length, placeholder detection, unique choices, answer-in-choices, giveaway prevention, no HTML/markdown, length bias, banned choices, punctuation)
- Three-layer question deduplication: session dedup (no repeats within session), global correct-answer dedup (never re-ask mastered questions), LLM prompt dedup
- Difficulty score display (1-10 dots + P(correct) percentage) at bottom of question card
- 41 new validator unit tests (95 total)
- Local clock SVG question generator ported from kidtutor — generates analog clock faces with hour/minute hands, no LLM needed for clock-reading curriculum nodes
- Two-panel session layout: left panel is the question, right panel shows previous answer result and per-node topic progress with mastery bars
- Session stats in top bar (correct/total + accuracy %)
- Global dedup model function `attempt.get_correct_texts()` for lifetime correct-answer tracking
- 1st Grade Math curriculum seed script (`scripts/seed_1st_grade_math.py`) with 31 nodes across 5 domains (OA, NBT, Measurement, Data, Geometry), full prerequisite chains, NJ standards-aligned

### Added
- Math answer verification (Rule 13): independently computes the correct answer for arithmetic questions and rejects LLM-generated questions where the answer is wrong — catches bugs like "7 less than 15 = 9" (should be 8)
- Supports 15+ question patterns: direct expressions (5+3), word operations (5 plus 3), phrased patterns (7 less than 15, subtract 3 from 10, sum of 6 and 8), missing number equations (__ + 5 = 12), three addends, unicode dash variants
- MCQ answer resolution: resolves letter answers (D) to option text (9) before verification
- Explanation vs answer cross-check (Rule 14): catches word problems where the LLM's explanation correctly computes the answer but the correct_answer field is wrong (e.g., explanation says "9 - 5 = 4" but answer says "3")
- Explanation arithmetic verification (Rule 15): verifies every "A op B = C" expression within the explanation is correct — catches "4 - 2 = 3" where both answer and explanation agree on a wrong value
- Word problem parsing: _try_compute_answer now handles "has N ... eats/gives/loses M" (subtraction), "has N ... gets/finds/bought M" (addition), and "there are N ... M fly away/left" patterns — covers 30+ verb forms
- 62 new tests for Rules 13-15: word problem parsing (12 subtraction verbs, 6 addition verbs, 5 "there are" patterns), explanation arithmetic (wrong/correct for +,-,*,/, chained ops, unicode, off-by-one, large numbers), consistently-wrong answer+explanation pairs, screenshot bug regression tests (286 total, was 224)
- Show original question text on the wrong-answer feedback page

### Added
- **Persist all state in SQLite** — sessions survive server restarts:
  - `skill_history` table: tracks every skill rating change over time, linked to the attempt that caused it
  - `sessions.current_question_id` + `sessions.last_result_json`: active session state persisted to DB, restored on resume
  - `attempts.skill_rating_before/after` + `attempts.curriculum_node_id`: full skill snapshot per attempt
  - Auto-migration: existing DBs get new columns via ALTER TABLE on startup
  - Question/feedback pages load from DB when flask_session is empty (after restart)
- Dual question pre-caching: pre-generates TWO questions per page load — one for correct answer (harder difficulty) and one for wrong answer (easier difficulty). Uses ELO prediction to simulate post-answer skill ratings without DB writes, then generates at appropriate difficulty for each outcome.
- 13 unit tests for dual cache behavior (correct/wrong path selection, different difficulties, partial None handling, overwrites, default path)

### Changed
- Faster calibration: base K 48→64, initial uncertainty 350→500, streak bonus at 2+ (was 3+), uncertainty decay 10%/attempt (was 5%), node advance after 2 correct at 85%+ (was 3) — app finds student's level in ~5 questions instead of 20+
- Enabled threaded mode in Flask dev server for concurrent precache + answer requests
- Increased max_generation_attempts from 2 to 3 — more retries since math verification rejects more bad questions
- Switched default model from qwen3:4b to qwen2.5 — qwen3's thinking mode generates thousands of invisible tokens (22s/question), qwen2.5 responds in <1s with valid JSON
- Removed ineffective /no_think prompt hack, added think:false API parameter as safety net for thinking-capable models
- Aggressive difficulty ramp-up: base K-factor 32→48, 2x streak bonus after 3+ consecutive correct, calibration 5x more aggressive, global streak/accuracy used across nodes (not just per-node), warm-start new nodes from student's proven level, faster node advancement (3 correct at 85%+ = move on)
- Tighter difficulty display scale (500-1100 ELO → 1-10) so progress is visible sooner — also makes LLM generate harder questions earlier
- Result card shows score delta (+3.9 green / -16.3 red) and topic progress delta after each answer
- Lowered initial skill rating from 1000 to 800 — students start with easiest questions, no prior knowledge assumed
- Raised initial uncertainty from 300 to 350 — faster skill adaptation in early questions
- Updated schema.sql defaults to match (800.0/350.0)
- Renamed project from "Moriah" to "Mora" everywhere (templates, config, DB file, spec, CSS, tests)
- Removed question limit — sessions now continue indefinitely until user clicks "End Session"
- Added topic mastery percentage (0-100%) at top of question and feedback pages, updates after every answer
- Enhanced LLM system prompt with 14 strict rules (from kidtutor): difficulty matching, single correct answer, no placeholder text, no banned choices, concise answers, punctuation requirements
- Rewrote spec.md to match implemented code — plain language only, no code snippets, covers all algorithms, data model, user flow, and frontend details

### Added
- Variety-first node selection: never repeat same curriculum node twice in a row, score candidates by need (low mastery), recency (not seen recently), and virgin bonus (new topics)
- Soft prerequisites: nodes accessible after 2 attempts on prerequisite (not just mastery)
- Visual-required node skip: 6 curriculum nodes disabled that need physical objects/images/charts
- Visual context detection (Rule 6b): rejects LLM questions containing phrases like "which is longer", "look at the picture", "use the graph"

### Fixed
- **Empty MCQ answer bug (Q365)**: `btn.disabled = true` in JS submit handler stripped the clicked button's value from form data — browser excludes disabled buttons from submission. Fix: removed `disabled`, using CSS `pointer-events: none` via `.submitting` class instead. Added server-side guard to reject empty answers.
- **Wrong question on feedback page**: After answering, `current_question` was already set to the NEXT question — feedback page showed wrong question text and generated explanation for the wrong question. Fix: feedback route now uses `result` data (answered question) instead of `current_question` (next question).
- **LLM intermediate answer bug (Q363)**: LLM set correct_answer to an intermediate computation step instead of the final answer (e.g., "3×4÷2" → answer "12" instead of "6"). Root cause: three validator gaps:
  - Rule 13 couldn't parse "multiplying X by Y then dividing by Z" or unicode operators (`×`, `÷`)
  - Rule 14 only found `= N` patterns, missed natural language ("to get 12", "which is 6")
  - Rule 13 couldn't parse "sum of X, Y, and Z" (comma-separated addends)
  - Fix: added unicode normalization, 7 new computation patterns (multiply/divide by, multi-step chains, product of, sum of N items), natural language result extraction in Rule 14. 33 new validator tests (365 total)
- **Double-submit race condition**: double-clicking an MCQ button sent two POSTs — first POST advanced to the next question, second POST checked the old answer against the new question's correct answer. Fix: 4-layer defense:
  - Server-side: `question_id` in form, reject submissions where form `question_id` != current question
  - Client-side: disable all choice buttons after first click, block keyboard shortcuts after submission
  - Template: hidden `question_id` field ties each submission to its question
  - UI: question ID (`Q#`) displayed on question and feedback pages for debugging
- **Duplicate questions bug**: after wrong answer with no precached question, `flask_session['current_question']` was not cleared — same question served repeatedly in a loop. Fix: explicitly clear question state after every answer, before setting the next one.
- Dedup strengthened: session exclude set now includes the current unanswered question (critical for precache path)
- 22 new dedup tests: session state clearing, dedup set construction, current question inclusion, consecutive duplicate detection, global dedup isolation, wrong-path regression tests (330 total)
- Feedback template referenced wrong route name (`session.next` → `session.next_question`)
- MCQ options displayed doubled letter prefix (added `strip_letter` Jinja2 filter)
- MCQ answer matching failed when LLM returned letter ("B") but student submitted text ("6") or vice versa — added text↔letter resolution using options list (6 new tests)
