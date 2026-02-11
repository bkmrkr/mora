# Mora Changelog

## [2026-02-11]

### Added
- Initial project structure: config, db, models, engine, ai, services, routes
- SQLite schema with 7 tables: students, topics, curriculum_nodes, sessions, questions, attempts, student_skill
- Database layer (get_db, init_db, query_db, execute_db)
- Configuration with ELO defaults, Ollama settings, session defaults

### Changed
- Renamed project from "Moriah" to "Mora" everywhere (templates, config, DB file, spec, CSS, tests)
- Removed question limit — sessions now continue indefinitely until user clicks "End Session"
- Added topic mastery percentage (0-100%) at top of question and feedback pages, updates after every answer
- Rewrote spec.md to match implemented code — plain language only, no code snippets, covers all algorithms, data model, user flow, and frontend details

### Fixed
- Feedback template referenced wrong route name (`session.next` → `session.next_question`)
- MCQ options displayed doubled letter prefix (added `strip_letter` Jinja2 filter)
