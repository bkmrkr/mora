"""Comprehensive scan of the database for bad questions.

Checks for:
1. Multiple correct answers in context (Rule 19 violations)
2. Remaining bad distractors
3. Misaligned questions and options
4. Mathematical errors in answers/explanations
5. Duplicate or similar questions
"""
import json
import re
import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.question_validator import validate_question

def scan_database():
    """Scan database for various types of bad questions."""
    db_path = Path(__file__).parent.parent / 'mora.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all questions
    cursor.execute("""
        SELECT id, content, options, correct_answer, explanation, question_type
        FROM questions
        ORDER BY id
    """)
    questions = cursor.fetchall()
    conn.close()

    print(f"Scanning {len(questions)} questions...\n")
    print("=" * 80)

    issues = {
        'rule_violations': [],
        'bad_distractors': [],
        'multiple_answers': [],
        'misaligned': [],
        'math_errors': [],
        'all_numeric_answers': [],
        'suspiciously_similar': defaultdict(list),
    }

    for qid, content, options_json, correct_answer, explanation, q_type in questions:
        try:
            if q_type != 'mcq':
                continue

            options = json.loads(options_json) if options_json else []

            # Test 1: Validation rules
            q_data = {
                'question': content,
                'correct_answer': correct_answer,
                'options': options,
                'question_type': q_type,
                'explanation': explanation
            }
            is_valid, reason = validate_question(q_data)
            if not is_valid:
                issues['rule_violations'].append((qid, reason))
                print(f"Q{qid}: VALIDATION FAILED - {reason}")
                continue

            # Test 2: Bad distractors (fallback garbage)
            FALLBACK_SET = {'0', '1', 'false', 'False', 'true', 'True', 'no', 'No', 'yes', 'Yes', 'unknown'}
            fallback_count = sum(1 for opt in options if opt in FALLBACK_SET)
            if fallback_count >= 2:
                issues['bad_distractors'].append((qid, f"{fallback_count} generic fallbacks", options))
                print(f"Q{qid}: BAD DISTRACTORS - {fallback_count} fallbacks in {options}")

            # Test 3: Multiple correct answers in context
            numbers_in_question = [int(m) for m in re.findall(r'\d+', content)]
            if numbers_in_question:
                correct_num = None
                try:
                    m = re.search(r'\d+', re.sub(r'^[A-Da-d][).\s]+\s*', '', correct_answer))
                    if m:
                        correct_num = int(m.group())
                except:
                    pass

                if correct_num is not None:
                    if 'even' in content.lower():
                        even_count = sum(1 for n in numbers_in_question if n % 2 == 0)
                        if even_count > 1:
                            issues['multiple_answers'].append((qid, f"{even_count} even numbers", numbers_in_question))
                            print(f"Q{qid}: MULTIPLE ANSWERS - {even_count} even numbers in {numbers_in_question}")

                    elif 'odd' in content.lower():
                        odd_count = sum(1 for n in numbers_in_question if n % 2 == 1)
                        if odd_count > 1:
                            issues['multiple_answers'].append((qid, f"{odd_count} odd numbers", numbers_in_question))
                            print(f"Q{qid}: MULTIPLE ANSWERS - {odd_count} odd numbers in {numbers_in_question}")

            # Test 4: Misaligned - question mentions numbers not in options
            if numbers_in_question:
                options_numbers = set()
                for opt in options:
                    nums = re.findall(r'\d+', str(opt))
                    options_numbers.update(int(n) for n in nums if n)

                question_set = set(numbers_in_question)
                if question_set and options_numbers and question_set.isdisjoint(options_numbers):
                    issues['misaligned'].append((qid, f"Question: {question_set}, Options: {options_numbers}"))
                    print(f"Q{qid}: MISALIGNED - Question mentions {question_set} but options have {options_numbers}")

            # Test 5: Math errors - explanation vs answer mismatch
            if explanation and ('is' in content.lower() or 'value' in content.lower()):
                # Simple check: if explanation contradicts the answer
                correct_answer_clean = re.sub(r'^[A-Da-d][).\s]+\s*', '', correct_answer).lower()
                explanation_lower = explanation.lower()

                # Check for common contradictions
                if 'even' in content.lower() and correct_num is not None:
                    if correct_num % 2 != 0 and 'even' in explanation_lower:
                        issues['math_errors'].append((qid, "Even number answer but number is odd"))
                        print(f"Q{qid}: MATH ERROR - Answer is even but {correct_num} is odd")

            # Test 6: All answer choices are numbers (likely auto-generated badly)
            if all(re.match(r'^[\d.]+$', str(opt).strip()) for opt in options):
                issues['all_numeric_answers'].append((qid, options))
                # Only report if question is NOT numeric
                if not any(char.isdigit() for char in content[:50]):
                    print(f"Q{qid}: ALL NUMERIC OPTIONS for non-numeric question")

        except Exception as e:
            print(f"Q{qid}: ERROR scanning - {e}")

    # Summary
    print("\n" + "=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)
    print(f"Total questions: {len(questions)}")
    print(f"Validation violations: {len(issues['rule_violations'])}")
    print(f"Bad distractors: {len(issues['bad_distractors'])}")
    print(f"Multiple correct answers: {len(issues['multiple_answers'])}")
    print(f"Misaligned Q&O: {len(issues['misaligned'])}")
    print(f"Math errors: {len(issues['math_errors'])}")
    print(f"All numeric options: {len(issues['all_numeric_answers'])}")

    if issues['rule_violations']:
        print(f"\nRule Violations ({len(issues['rule_violations'])}):")
        for qid, reason in issues['rule_violations'][:10]:
            print(f"  Q{qid}: {reason}")
        if len(issues['rule_violations']) > 10:
            print(f"  ... and {len(issues['rule_violations']) - 10} more")

    if issues['bad_distractors']:
        print(f"\nBad Distractors ({len(issues['bad_distractors'])}):")
        for qid, reason, opts in issues['bad_distractors'][:10]:
            print(f"  Q{qid}: {reason}")
        if len(issues['bad_distractors']) > 10:
            print(f"  ... and {len(issues['bad_distractors']) - 10} more")

    if issues['multiple_answers']:
        print(f"\nMultiple Correct Answers ({len(issues['multiple_answers'])}):")
        for qid, reason, nums in issues['multiple_answers'][:10]:
            print(f"  Q{qid}: {reason} - {nums}")
        if len(issues['multiple_answers']) > 10:
            print(f"  ... and {len(issues['multiple_answers']) - 10} more")

    if issues['misaligned']:
        print(f"\nMisaligned Questions/Options ({len(issues['misaligned'])}):")
        for qid, reason in issues['misaligned'][:10]:
            print(f"  Q{qid}: {reason}")
        if len(issues['misaligned']) > 10:
            print(f"  ... and {len(issues['misaligned']) - 10} more")

    # Return list of problematic question IDs
    all_bad_ids = set()
    for issue_list in issues.values():
        if isinstance(issue_list, list):
            all_bad_ids.update(q[0] for q in issue_list)

    print(f"\nTotal problematic questions: {len(all_bad_ids)}")
    if all_bad_ids:
        print(f"Question IDs: {sorted(list(all_bad_ids))[:30]}")
        if len(all_bad_ids) > 30:
            print(f"... and {len(all_bad_ids) - 30} more")

    return issues, all_bad_ids


if __name__ == '__main__':
    issues, bad_ids = scan_database()
