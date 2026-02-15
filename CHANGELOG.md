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
