#!/usr/bin/env python3
"""Validate every question in the DB against the question_validator rules.

No LLM calls — purely deterministic. Reports pass/fail counts grouped by rule.
Exit code 1 if any failures.

Usage:
    python3 scripts/validate_questions.py
"""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import query_db, init_db
from engine.question_validator import validate_question


def main():
    init_db()

    questions = query_db("SELECT * FROM questions ORDER BY id")
    if not questions:
        print("No questions in database.")
        return 0

    total = len(questions)
    passed = 0
    failed = 0
    failures_by_reason = {}

    for q in questions:
        q_data = {
            'question': q['content'],
            'correct_answer': q['correct_answer'],
            'options': json.loads(q['options']) if q['options'] else None,
            'explanation': q.get('explanation', ''),
        }

        is_valid, reason = validate_question(q_data)

        if is_valid:
            passed += 1
        else:
            failed += 1
            failures_by_reason.setdefault(reason, []).append(q['id'])
            print(f"  FAIL Q{q['id']}: {reason}")
            print(f"        Question: {q['content'][:80]}")
            print(f"        Answer:   {q['correct_answer']}")
            print()

    print("=" * 60)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)

    if failures_by_reason:
        print("\nFailures by rule:")
        for reason, qids in sorted(failures_by_reason.items(), key=lambda x: -len(x[1])):
            print(f"  [{len(qids):3d}] {reason}")
            print(f"        Question IDs: {', '.join(str(q) for q in qids[:10])}"
                  f"{'...' if len(qids) > 10 else ''}")

    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
