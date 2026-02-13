"""Fix questions with nonsensical distractors in the database.

Finds all questions with bad distractor patterns and either:
1. Attempts to regenerate with new distractor logic
2. Deletes the question if regeneration fails
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.distractors import insert_distractors
from engine.question_validator import verify_distractor_quality

# Known fallback values that indicate poor distractor generation
FALLBACK_SET = {'0', '1', 'false', 'False', 'true', 'True', 'no', 'No', 'yes', 'Yes', 'unknown'}


def needs_fixing(options_json, correct_answer):
    """Check if a question has bad distractors."""
    try:
        options = json.loads(options_json)
    except json.JSONDecodeError:
        return True, "Invalid JSON in options"

    if not isinstance(options, list):
        return True, "Options not a list"

    fallback_count = sum(1 for opt in options if opt in FALLBACK_SET)

    # 2+ fallbacks = definitely bad
    if fallback_count >= 2:
        return True, f"{fallback_count} generic fallbacks"

    # Hebrew/LaTeX/special with any fallback = bad
    has_hebrew = bool(re.search(r'[\u0590-\u05FF]', correct_answer))
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', correct_answer))
    has_latex = bool(re.search(r'\\[a-z]+\{', correct_answer))
    has_special = has_hebrew or has_arabic or has_latex

    if has_special and fallback_count > 0:
        return True, f"Special text + {fallback_count} fallback"

    return False, ""


def fix_question(question_id, content, correct_answer):
    """Attempt to regenerate distractors for a question.

    Returns: ('fixed', None), ('deleted', reason), or ('failed', reason)
    """
    q_data = {
        'question': content,
        'correct_answer': correct_answer,
        'question_type': 'mcq',
        'explanation': 'Explanation'  # Dummy for validation
    }

    # Try to generate new distractors
    try:
        result, success, reason = insert_distractors(q_data)
        if not success:
            return 'failed', reason
    except Exception as e:
        return 'failed', str(e)

    # Validate the new distractors
    is_valid, reason = verify_distractor_quality(result)
    if not is_valid:
        return 'failed', f"Validation failed: {reason}"

    # Success - return the new options
    return 'fixed', result['options']


def main():
    db_path = Path(__file__).parent.parent / 'mora.db'
    print(f"Analyzing questions in {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find all MCQ questions
    cursor.execute("""
        SELECT id, content, correct_answer, options
        FROM questions
        WHERE question_type = 'mcq'
        ORDER BY id
    """)

    questions = cursor.fetchall()
    total = len(questions)
    affected = []
    fixed = []
    deleted = []
    failed = []

    print(f"\nScanning {total} MCQ questions...\n")

    for qid, content, correct_answer, options_json in questions:
        needs_fix, reason = needs_fixing(options_json, correct_answer)

        if needs_fix:
            affected.append((qid, reason))
            print(f"Q{qid}: {reason}")

            # Try to fix
            status, info = fix_question(qid, content, correct_answer)

            if status == 'fixed':
                # Update database
                new_options_json = json.dumps(info)
                try:
                    cursor.execute(
                        "UPDATE questions SET options = ? WHERE id = ?",
                        (new_options_json, qid)
                    )
                    conn.commit()
                    fixed.append(qid)
                    print(f"  ✓ FIXED with new distractors")
                except Exception as e:
                    failed.append((qid, str(e)))
                    print(f"  ✗ FAILED to update: {e}")

            elif status == 'failed':
                # Can't regenerate - delete question
                try:
                    cursor.execute("DELETE FROM questions WHERE id = ?", (qid,))
                    conn.commit()
                    deleted.append((qid, info))
                    print(f"  ✗ DELETED (cannot regenerate): {info}")
                except Exception as e:
                    failed.append((qid, str(e)))
                    print(f"  ✗ FAILED to delete: {e}")

    conn.close()

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total questions:     {total}")
    print(f"With bad distractors: {len(affected)}")
    print(f"Fixed:              {len(fixed)}")
    print(f"Deleted:            {len(deleted)}")
    print(f"Failed:             {len(failed)}")

    if affected:
        print(f"\nAffected question IDs: {[q[0] for q in affected]}")

    if deleted:
        print(f"\nDeleted questions:")
        for qid, reason in deleted:
            print(f"  Q{qid}: {reason}")

    if failed:
        print(f"\nFailed to process:")
        for qid, reason in failed:
            print(f"  Q{qid}: {reason}")

    return len(failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
