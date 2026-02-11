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

- Run `python3 -m pytest tests/ -v` before committing
- All tests must pass

## Architecture

Layered: config → db → models → engine (pure functions) → ai → services → routes. Each layer only depends on layers below it.
