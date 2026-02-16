# Mora v2 Changelog

### Hardened — Tighten CSP script-src
- Removed `'unsafe-inline'` from `script-src` in Content-Security-Policy header
- No inline scripts exist — all JS loaded via external `session.js`
- `style-src 'unsafe-inline'` kept (needed for mastery bar widths, clock centering)
- Verified: keyboard shortcuts, response time tracking, and all JS features still work

### Fixed — NULL total_correct in Empty Sessions
- `end_session()` stored NULL instead of 0 for `total_correct` when session had no attempts
- SQL `SUM()` returns NULL for 0 rows — added `COALESCE(..., 0)` to handle this
- Dashboard now filters out 0-question sessions in the route (not just template)
- Prevents empty "Recent Sessions" table from showing for students with no answered questions

### Fixed — Case-Sensitive Student Name Matching
- Typing "sophia" created a new student instead of matching existing "Sophia"
- `get_by_name()` now uses `COLLATE NOCASE` for case-insensitive lookup
- Schema updated with `COLLATE NOCASE` on `students.name` for new databases
- Verified: XSS in name field safely escaped by Jinja2 auto-escaping

### Improved — Clock SVG Accessibility
- Added `role="img"` and `aria-label="Clock face"` to clock SVG element
- Screen readers now announce the clock image properly

### Fixed — Short Answer Mode Was Unreachable
- Short answer threshold (0.7) was higher than mastery threshold (0.65)
- Skills got mastered and excluded from the eligible pool before reaching 0.7
- Lowered short answer threshold to 0.5 — students type answers once they're getting ~50% right on a skill
- Verified in Playwright: text input renders, correct/wrong answers graded, feedback works

### Fixed — Dashboard Shows "No Students" for Invalid Student ID
- `/dashboard/999` rendered empty index template saying "No students yet"
- Now redirects to `/dashboard/` which shows the actual student list

### Added — Styled Error Pages (404/500)
- Created `templates/error.html` extending `base.html` — proper nav, "Go Home" button
- Error handler now renders template instead of Flask's bare default HTML
- 404 and 500 pages show consistent app styling

### Fixed — Ended Sessions Could Be Resumed via Direct URL
- Navigating to `/session/<ended_id>/question` would generate new questions for an ended session
- Added `ended_at` guard to question, answer, feedback, and next_question routes
- Ended sessions now redirect to the summary page

### Fixed — session.js Not Loaded, Keyboard Shortcuts Broken
- `session.js` was never included in `question.html` — only an inline script for response time existed
- Missing features: keyboard shortcuts (A/B/C/D), double-submit prevention, button disable on submit
- Added `data-key` attributes (A/B/C/D) to MCQ buttons in template
- Replaced inline script with `<script src="session.js">` to load all features
- Verified with Playwright: keyboard shortcuts, response time, and navigation all work

### Hardened — Cookie Validation Requires question_type
- Answer route and question route now require `question_type` in session cookie validation
- Previously, a tampered cookie missing `question_type` caused `KeyError` crash in `answer_service.py`
- Added to both `required_keys` checks in `routes/session.py`

### Fixed — Error Handler Swallowed HTTP Status Codes
- Catch-all `@app.errorhandler(Exception)` was converting 404 Not Found to 500 Internal Server Error
- Now re-raises `HTTPException` subclasses (404, 405, etc.) with their correct status codes
- Only non-HTTP exceptions return 500

### Fixed — Non-Numeric response_time_s Crashed Answer Route
- `float(request.form.get('response_time_s', 0))` crashed with `ValueError` on non-numeric input ('abc', '', etc.)
- Now wrapped in try/except, defaults to 0.0 on invalid input

### Hardened — NaN/Inf Guards in ELO Functions
- All ELO functions (p_correct, compute_k_factor, update_skill, compute_mastery) now guard against NaN/Inf inputs
- Corrupted data falls back to safe defaults (800.0 for ratings, initial values for uncertainty)
- NaN can never enter through normal operation paths — guards are purely defensive

### Fixed — Fraction Equivalence in Short Answer Mode
- `_to_number()` now parses fractions like "1/2" → 0.5, so "2/4" is accepted when answer is "1/2"
- Also handles fraction-to-decimal comparison ("3/4" matches "0.75")
- Handles division by zero safely ("5/0" returns None)

### Fixed — Mastery Progression Too Slow
- Mastery formula overweighted ELO rating (60%) vs actual accuracy (40%) — student with 100% accuracy after 31 questions still couldn't unlock Grade 2
- Changed mastery weights to 0.3 rating / 0.7 accuracy — accuracy-dominant for faster progression
- Lowered mastery threshold from 0.75 to 0.65 — 80% accuracy students (the target rate) can now progress
- Added `min_attempts=5` gate to prevent mastering a skill with 1-2 lucky answers
- Result: perfect student masters a skill in ~5 questions; 80% student masters in ~5-8; 70% student stays put

### Fixed — Template Content Bugs (found via stress testing)
- g1_shapes: "What shape has 4 sides?" accepted only square OR rectangle — now only asks about shapes with unique side counts (triangle=3, hexagon=6)
- g2_odd_even: "Which number is odd?" showed multiple odd numbers in options but only one was accepted — now generates exactly 1 correct + 3 opposite-parity options
- g3_data: "Most popular pet?" had 26% chance of tied values with only one accepted — now uses unique values (`random.sample`)
- g3_elapsed_time: Showed 24-hour format ("ends at 13:00") and confusing 12-hour wraparound ("starts at 10:00, ends at 2:00") — now limits start time so end never exceeds 12

## [2026-02-15] — v2 Rewrite: Math-Only, Template-Based

Complete rewrite from multi-subject LLM-based system to math-only template-based system.

### Why
LLM (qwen2.5) could not reliably produce grade-appropriate educational content. After 10 phases of pipeline rebuilding, the fundamental problem remained: misleveled questions, broken options, and unpredictable output. Template-based generation is correct by construction.

### Added — Phase 1: DB + Models + Curriculum
- New 5-table schema: students, student_progress, sessions, questions, attempts
- `curriculum/skills.py` — 40 math skills across grades 1-4 with prerequisite DAG
- `models/progress.py` — upsert-based skill progress tracking (replaces student_skill.py)
- 88 tests (models + curriculum structure + DAG validation)

### Added — Phase 2: ELO Engine + Skill Selector
- `engine/selector.py` — prerequisite-gated skill selection with variety, virgin bonus, warm-start
- Kept unchanged: `engine/elo.py`, `engine/difficulty.py`, `engine/answer_matching.py`
- 16 selector tests (104 total)

### Added — Phase 3: Grade 1 Templates
- `curriculum/templates/grade1.py` — 10 template functions (add/sub 10/20, place value, counting, comparing, time, shapes, word problems)
- `curriculum/templates/common.py` — distractor generation (off-by-one, wrong-operation patterns), option shuffling, word problem frames
- Difficulty-aware: templates scale parameters based on ELO (e.g., max_sum=7 at low ELO, 10 at high)
- 15 template tests (119 total)

### Added — Phase 4: Services
- `services/question_service.py` — select skill → pick template → generate → store (no LLM)
- `services/answer_service.py` — grade answer → ELO update → record attempt (no LLM grading)
- 9 service tests (128 total)

### Added — Phase 5: Routes + UI
- `app.py` — simplified (3 blueprints, no admin, no Ollama)
- `routes/home.py` — name entry + returning student chips → start session
- `routes/session.py` — question → answer → feedback (wrong only) → next → end summary
- `routes/dashboard.py` — grade-by-grade progression with per-skill mastery bars
- All templates rewritten for math-only flow
- `make_options()` deduplication fix — guaranteed 4 unique options even with small numbers
- 20 route tests (148 total)

### Added — Phase 6: Grades 2-4 Templates
- `curriculum/templates/grade2.py` — 10 templates (add/sub 100/1000, intro multiply, money, time, measurement, fractions intro, comparing 3-digit, two-step, odd/even)
- `curriculum/templates/grade3.py` — 10 templates (mult/div facts, multi-digit mult, area/perimeter, fraction compare/add/sub, rounding, word problems, elapsed time, data interpretation)
- `curriculum/templates/grade4.py` — 10 templates (2x2 mult, long division, fraction ops with unlike denom, decimal place value/add/sub, angles, geometry, factors/multiples, multi-step word, equivalent fractions)
- `make_options()` extended: fraction distractor padding and decimal distractor padding
- 31 new tests (179 total)

### Verified — Phase 8: Playwright Browser Testing
- Full flow walked in real browser: home → start → question → correct (skip feedback) → wrong → feedback → next → end → summary → dashboard
- All 11 checkpoints pass: home page, question rendering, correct answer flow, wrong answer flow, feedback page, session summary, dashboard overview, dashboard index, returning student chip, session stats, console errors (zero)
- Grade-by-grade dashboard shows all 40 skills with mastery bars and ELO ratings

### Added — Phase 7: Integration Test
- `tests/test_integration.py` — full 20-question student journey via Flask test client
- Verifies: session lifecycle, ELO rating updates, attempt persistence, skill variety, dashboard display, student persistence across sessions, feedback flow (correct skips, wrong shows), accuracy calculation, returning student chips
- All 40 skills verified: registered in service, every template produces valid 4-option MCQ
- 10 integration tests (189 total)

### Added — Clock SVG Visuals for Time Questions
- `common.py`: `generate_clock_svg(hour, minute)` renders analog clock face with hour/minute hands
- Ported from kidtutor project — circle, tick marks, numbers, hour hand (thick), minute hand (thin), center dot
- Grade 1 (`g1_time`) and Grade 2 (`g2_time`) templates now show clock image instead of text like "A clock shows 12 o'clock"
- Question text changed to "What time does this clock show?" — no more giving away the answer
- Clock params (`clock_hour`, `clock_minute`) stored in session cookie (8 bytes vs ~2KB SVG), SVG regenerated at render time
- Verified with Playwright: clock renders correctly in browser

### Added — Intrinsic Difficulty Scoring
- `common.py`: `estimate_difficulty(grade, complexity)` maps grade (1-4) + complexity (0.0-1.0) to ELO difficulty
- Grade bands: G1 500-750, G2 700-950, G3 900-1150, G4 1100-1350
- All 40 templates now return a `difficulty` field based on actual question parameters (operand size, number of steps, denominator size, etc.)
- `question_service.py` uses intrinsic difficulty instead of target difficulty for ELO calculations
- Result: "2 + 1" gets difficulty ~525, "7 × 8" gets ~962, "1/2 + 1/4" gets ~1242

### Fixed — Stale Session Cookie Bug
- `routes/home.py`: clear Flask session on `/start` to purge stale v1 cookies
- `routes/session.py`: validate `current_question` has required v2 fields (`skill_id`, `question_id`, `correct_answer`, `options`) before using; discard and regenerate if invalid
- `routes/session.py`: `answer()` route redirects to question page (not end page) if session data is invalid
- Root cause: browser retained v1 session cookie with `current_question` missing `skill_id` field, causing `KeyError` in `answer_service.py`
- Verified fix with Playwright: full flow (home → start → correct → wrong → feedback → next → end → summary → dashboard) works with zero errors

### Removed
- All `ai/` modules (question_generator, json_utils, explainer, answer_grader, local_generators)
- Admin blueprint and templates
- LLM-related DB columns (generated_prompt, model_used, test_status, validation_error, quality_flags)
- Tables: topics, curriculum_nodes, question_reports, skill_history
- Precache system, similarity dedup, question validator (templates are correct by construction)
- Ollama configuration and warm-up
- `render_math`, `render_md_bold` template filters
- `scripts/` directory (generate, validate, seed scripts)
- `services/onboarding_service.py`, `services/math_renderer.py`
- 23 v1 test files

---

## v1 History (2026-02-11 to 2026-02-15)

See git history for the full v1 changelog. Key milestones:
- Multi-subject adaptive learning (Math, Reading, Science, Social Studies, Hebrew)
- LLM-based question generation with qwen2.5 via Ollama
- 10 phases of pipeline rebuilding to fix 97.7% broken question rate
- Final state: 441 tests, 247 validated questions, but fundamentally unreliable LLM output
