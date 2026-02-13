"""Test question generation and validate each question."""
import requests
import re

s = requests.Session()

# Start session
resp = s.post('http://localhost:5002/session/start', data={
    'student_id': '1',
    'topic_id': '3'
}, allow_redirects=True)
session_id = resp.url.split('/')[4]
print(f'Session: {session_id}')
print('='*60)

results = []

for i in range(15):
    print(f'\n--- Question {i+1} ---')
    resp = s.get(f'http://localhost:5002/session/{session_id}/question')
    html = resp.text

    # Check if session ended
    if '/end' in resp.url:
        print('Session ended!')
        break

    # Extract question
    q_match = re.search(r'class="question-text"[^>]*>([^<]+)<', html)
    q_text = q_match.group(1).strip() if q_match else 'Not found'
    print(f'Q: {q_text[:100]}...')

    # Question ID
    qid_match = re.search(r'question_id.*?value="(\d+)"', html)
    qid = qid_match.group(1) if qid_match else '?'

    # Extract options
    opts = re.findall(r'<button[^>]*value="([^"]+)"[^>]*data-key="([^"]+)"', html)
    print(f'Options: {[(v, k) for v, k in opts]}')

    # Get difficulty from DB
    import sqlite3
    conn = sqlite3.connect('mora.db')
    cur = conn.cursor()
    cur.execute('SELECT difficulty, correct_answer FROM questions WHERE id = ?', (qid,))
    row = cur.fetchone()
    if row:
        print(f'Difficulty: {row[0]}, Correct: {row[1]}')
        results.append({
            'num': i+1,
            'qid': qid,
            'question': q_text[:50],
            'options': [v for v, k in opts],
            'correct': row[1],
            'difficulty': row[0]
        })
    conn.close()

    # Submit a random answer (simulating 75% correct)
    import random
    correct_answer = row[1] if row else 'A'
    # Determine if we want correct or wrong
    is_correct = random.random() < 0.75

    if is_correct:
        # Find the correct option
        for opt_val, opt_key in opts:
            # Match option value to correct answer
            if opt_val.strip() in correct_answer or correct_answer in opt_val:
                answer = opt_key
                break
        else:
            answer = opts[0][1] if opts else 'A'
    else:
        # Pick wrong answer
        if len(opts) > 1:
            answer = opts[1][1] if is_correct else random.choice([k for v, k in opts])
        else:
            answer = 'A'

    print(f'Answering: {answer} (target: {"correct" if is_correct else "wrong"})')

    resp = s.post(f'http://localhost:5002/session/{session_id}/answer', data={
        'question_id': qid,
        'answer': answer,
        'response_time_s': str(random.randint(2, 8))
    }, allow_redirects=True)

    if 'feedback' in resp.url:
        print('-> Wrong')
    elif 'question' in resp.url:
        print('-> Correct!')

print('\n' + '='*60)
print('SUMMARY')
print('='*60)
for r in results:
    print(f"Q{r['num']}: diff={r['difficulty']:.0f}, correct={r['correct'][:20]}...")
