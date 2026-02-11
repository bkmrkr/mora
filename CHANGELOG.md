# Moriah Changelog

## [2026-02-11]

### Added
- Initial project structure: config, db, models, engine, ai, services, routes
- SQLite schema with 7 tables: students, topics, curriculum_nodes, sessions, questions, attempts, student_skill
- Database layer (get_db, init_db, query_db, execute_db)
- Configuration with ELO defaults, Ollama settings, session defaults

### Fixed
- Feedback template referenced wrong route name (`session.next` → `session.next_question`)
- MCQ options displayed doubled letter prefix (added `strip_letter` Jinja2 filter)
