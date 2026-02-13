"""Test script to analyze question quality for 10-15 questions."""
import requests
import sqlite3
import re

BASE_URL = 'http://localhost:5002'
DB_PATH = 'mora.db'

def analyze_question(html, question_id):
    """Analyze a question for quality issues."""
    issues = []

    # Find question text
    q_match = re.search(r'class="question-text"[^>]*>([^<]+)<', html)
    if q_match:
        q_text = q_match.group(1).strip()
    else:
        q_text = "Unknown"

    # Find options
    opts = re.findall(r'<button[^>]*value="([^"]+)"[^>]*data-key="([A-D])"', html)

    # Check for HTML entities (unrendered math)
    if '&' in q_text or '&gt;' in q_text or '&lt;' in q_text:
        issues.append("WARNING: Contains HTML entities (unrendered LaTeX)")

    # Check for visual/draw requirements
    visual_keywords = ['graph', 'draw', 'show', 'picture', 'image', 'diagram']
    for kw in visual_keywords:
        if kw in q_text.lower():
            issues.append(f"WARNING: Contains '{kw}' - may require visual")

    # Check for placeholder text
    placeholder_patterns = ['[shows', '[image', '[picture', '[display']
    for pat in placeholder_patterns:
        if pat in q_text.lower():
            issues.append(f"WARNING: Contains placeholder: {pat}")

    # Check options for validity
    if opts:
        # Extract option values
        opt_values = [o[0] for o in opts]

        # Check if options are all the same
        if len(set(opt_values)) < len(opt_values):
            issues.append("ERROR: Duplicate options!")

        # Check for empty options
        empty_opts = [o for o in opt_values if not o.strip()]
        if empty_opts:
            issues.append(f"ERROR: {len(empty_opts)} empty options")

    return q_text, opts, issues


def get_correct_answer_from_db(question_id):
    """Get the correct answer from database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT content, correct_answer, options, difficulty FROM questions WHERE id = ?', (question_id,))
    row = cur.fetchone()
    conn.close()
    return row


def main():
    s = requests.Session()

    print("=== Starting test session ===\n")

    # Start session with 1st Grade Math
    resp = s.post(f'{BASE_URL}/session/start', data={
        'student_id': '1',
        'topic_id': '3'  # 1st Grade Math
    }, allow_redirects=True)

    # Extract session ID
    parts = resp.url.split('/')
    session_id = parts[4]
    print(f"Session: {session_id}\n")

    results = []

    for i in range(12):
        print(f"--- Question {i+1} ---")

        # Get question page
        resp = s.get(f'{BASE_URL}/session/{session_id}/question')
        html = resp.text

        # Check if session ended
        if '/end' in resp.url:
            print("Session ended!")
            break

        # Find question ID
        qid_match = re.search(r'question_id.*?value="(\d+)"', html)
        if not qid_match:
            print("ERROR: Could not find question ID")
            continue

        question_id = int(qid_match.group(1))

        # Analyze question
        q_text, opts, issues = analyze_question(html, question_id)
        print(f"Q{question_id}: {q_text[:60]}...")

        # Get correct answer from DB
        db_row = get_correct_answer_from_db(question_id)
        if db_row:
            correct_answer = db_row[1]
            difficulty = db_row[3]
            print(f"  Correct: {correct_answer}")
            print(f"  Difficulty: {difficulty:.2f}" if difficulty else "  Difficulty: N/A")
        else:
            print("  ERROR: Could not find in DB")
            correct_answer = None

        # Show options
        if opts:
            print(f"  Options: {[o[0][:15] for o in opts]}")

        # Report issues
        if issues:
            for issue in issues:
                print(f"  {issue}")

        # Answer question (simulate ~75% correct by alternating)
        is_correct = (i % 4 != 3)  # 75% correct

        # Find which option is correct
        if correct_answer and opts:
            # Try to find matching option
            answer_letter = None
            for opt_val, letter in opts:
                # Check if option matches correct answer
                if correct_answer.strip() == opt_val.strip():
                    answer_letter = letter
                    break
                # Check without letter prefix
                for prefix in ['A) ', 'B) ', 'C) ', 'D) ']:
                    if correct_answer.strip() == prefix + opt_val.strip():
                        answer_letter = letter
                        break

            # If not found, just pick one
            if not answer_letter:
                answer_letter = 'A' if is_correct else 'B'
        else:
            answer_letter = 'A'

        print(f"  -> Answering: {answer_letter} ({'CORRECT' if is_correct else 'WRONG'})")

        # Submit answer
        resp = s.post(f'{BASE_URL}/session/{session_id}/answer', data={
            'question_id': str(question_id),
            'answer': answer_letter,
            'response_time_s': '3'
        }, allow_redirects=True)

        if 'feedback' in resp.url:
            print("  -> Feedback page (wrong)")
        elif 'question' in resp.url:
            print("  -> Next question (correct)")
        else:
            print("  -> Session ended")

        print()
        results.append({
            'question_id': question_id,
            'difficulty': difficulty,
            'issues': issues,
            'correct': is_correct
        })

    # Summary
    print("\n=== SUMMARY ===")
    total = len(results)
    correct = sum(1 for r in results if r['correct'])
    print(f"Total questions: {total}")
    print(f"Correct: {correct} ({correct/total*100:.0f}%)")

    # Difficulty range
    diffs = [r['difficulty'] for r in results if r['difficulty']]
    if diffs:
        print(f"Difficulty range: {min(diffs):.2f} - {max(diffs):.2f}")

    # Issues
    all_issues = []
    for r in results:
        all_issues.extend(r['issues'])

    if all_issues:
        print(f"\nIssues found: {len(all_issues)}")
        for issue in set(all_issues):
            count = all_issues.count(issue)
            print(f"  - {issue}: {count}x")
    else:
        print("\nNo issues found!")


if __name__ == '__main__':
    main()
