# Mora Changelog

## [2026-02-11]

### Added
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

### Changed
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
