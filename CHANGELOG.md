# Mora Changelog

## [2026-02-11]

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
- **Duplicate questions bug**: after wrong answer with no precached question, `flask_session['current_question']` was not cleared — same question served repeatedly in a loop. Fix: explicitly clear question state after every answer, before setting the next one.
- Dedup strengthened: session exclude set now includes the current unanswered question (critical for precache path)
- 22 new dedup tests: session state clearing, dedup set construction, current question inclusion, consecutive duplicate detection, global dedup isolation, wrong-path regression tests (330 total)
- Feedback template referenced wrong route name (`session.next` → `session.next_question`)
- MCQ options displayed doubled letter prefix (added `strip_letter` Jinja2 filter)
- MCQ answer matching failed when LLM returned letter ("B") but student submitted text ("6") or vice versa — added text↔letter resolution using options list (6 new tests)
