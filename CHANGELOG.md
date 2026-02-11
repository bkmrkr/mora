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
- 72 new tests for math verifier + explanation cross-check (175 total, was 103)
- Show original question text on the wrong-answer feedback page

### Added
- Question pre-caching: JS fires async POST to `/precache` on page load, server pre-generates next question while student thinks — eliminates 1-3s wait between questions
- 10 unit tests for cache behavior (pop_cached empty/hit/miss, node match/mismatch, overwrites, wrong student/session)

### Changed
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

### Fixed
- Feedback template referenced wrong route name (`session.next` → `session.next_question`)
- MCQ options displayed doubled letter prefix (added `strip_letter` Jinja2 filter)
- MCQ answer matching failed when LLM returned letter ("B") but student submitted text ("6") or vice versa — added text↔letter resolution using options list (6 new tests)
