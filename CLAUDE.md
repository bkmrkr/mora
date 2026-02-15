# Mora Project Instructions

## Git Workflow

After completing meaningful changes, commit and push to origin:
```
git add <files> && git commit -m "message" && git push origin main
```

- Commit after each logical unit of work (don't accumulate)
- Push to `origin main` after committing
- Update CHANGELOG.md with each change

## Remote

- Repository: https://github.com/bkmrkr/mora.git
- Branch: main

## Testing

- **Run `python3 -m pytest tests/ -v` after every code change and before committing** — not just at the end, but after each file edit or logical step
- All tests must pass before committing
- When adding new features, write tests first or alongside the code
- Test categories: models (DB CRUD), engine (pure functions), templates (grade 1-4), services (integration), routes (HTTP flow), integration (full student journey)
- 189 tests across 14 test files

## Architecture

Mora v2: math-only, template-based adaptive learning for grades 1-4. Zero LLM.

Layered: config → db → models → engine (pure functions) → curriculum/templates → services → routes. Each layer only depends on layers below it.

- **config/**: ELO defaults, DB path
- **db/**: SQLite schema (5 tables), database helpers
- **models/**: student, progress, session, question, attempt (CRUD)
- **engine/**: elo, difficulty, answer_matching, selector (pure functions)
- **curriculum/**: 40 skills in skills.py, templates/ with grade1-4.py + common.py
- **services/**: question_service (select skill → template → store), answer_service (grade → ELO → persist)
- **routes/**: home (3 blueprints), session, dashboard
- **templates/**: Jinja2 HTML (home, session/question, session/feedback_wrong, session/summary, session/retry, dashboard/index, dashboard/overview)
