# Mora v2 Changelog

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
