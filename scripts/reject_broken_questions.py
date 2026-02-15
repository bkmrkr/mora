#!/usr/bin/env python3
"""Reject questions with broken placeholder options ["A","B","C","D"].

One-time cleanup script. Marks broken MCQ questions as rejected so they
are never served to students. Does NOT delete — preserves for audit.

Usage:
    python3 scripts/reject_broken_questions.py [--dry-run]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import query_db, execute_db, init_db

PLACEHOLDER_OPTIONS = ['A', 'B', 'C', 'D']


def main():
    dry_run = '--dry-run' in sys.argv
    init_db()

    questions = query_db(
        "SELECT id, content, correct_answer, options FROM questions "
        "WHERE question_type = 'mcq' AND test_status != 'rejected'"
    )

    total = len(questions)
    broken = []

    for q in questions:
        opts = json.loads(q['options']) if q['options'] else None

        if not opts or not isinstance(opts, list):
            broken.append((q['id'], 'missing options'))
            continue

        if opts == PLACEHOLDER_OPTIONS:
            broken.append((q['id'], 'placeholder ["A","B","C","D"]'))
            continue

        correct = q['correct_answer'] or ''
        if correct and correct not in opts:
            broken.append((q['id'], f'answer "{correct}" not in options'))
            continue

    print(f"Total MCQ questions: {total}")
    print(f"Broken questions:    {len(broken)}")

    if not broken:
        print("No broken questions found.")
        return 0

    if dry_run:
        print("\n[DRY RUN] Would reject:")
        for qid, reason in broken[:20]:
            print(f"  Q{qid}: {reason}")
        if len(broken) > 20:
            print(f"  ... and {len(broken) - 20} more")
        return 0

    ids = [b[0] for b in broken]
    placeholders = ','.join('?' * len(ids))
    execute_db(
        f"UPDATE questions SET test_status = 'rejected', "
        f"validation_error = 'Phase 5 cleanup: broken MCQ options' "
        f"WHERE id IN ({placeholders})", ids
    )

    print(f"\nRejected {len(broken)} questions.")

    # Summarize by reason
    reasons = {}
    for _, reason in broken:
        reasons[reason] = reasons.get(reason, 0) + 1
    print("\nBreakdown:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  [{count:3d}] {reason}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
