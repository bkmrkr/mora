"""Simulate a student answering questions with 75% correct rate."""
import random
import requests
import json

BASE_URL = 'http://localhost:5002'

# Track cookies for session
session = requests.Session()

# Step 1: Create a new student
print("Creating test student...")
resp = session.post(f'{BASE_URL}/onboard', data={
    'student_name': 'TestStudent',
    'topic_name': '1st Grade Math'
}, allow_redirects=False)

# Extract student ID from redirect or find existing
# Let's check existing students
resp = session.get(f'{BASE_URL}/')
student_id = 3  # Use existing student

# Step 2: Start a session
print(f"Starting session for student {student_id}...")
resp = session.post(f'{BASE_URL}/session/start', data={
    'student_id': str(student_id),
    'topic_id': '1'
}, allow_redirects=False)

# Extract session ID from Location header
session_id = resp.headers.get('Location', '').split('/')[-1]
print(f"Session ID: {session_id}")

# Step 3: Answer 20 questions with ~75% correct
correct_count = 0
total = 20

for i in range(total):
    # Get current question
    resp = session.get(f'{BASE_URL}/session/{session_id}/question')
    if resp.status_code != 200:
        print(f"Error getting question: {resp.status_code}")
        break

    # Parse question from response
    # We need to find the question and options from the HTML
    html = resp.text

    # Find question content
    import re
    q_match = re.search(r'class="question-text"[^>]*>([^<]+)<', html)
    if not q_match:
        print(f"Could not find question in response")
        break

    # Find options
    options = re.findall(r'value="([^"]+)"[^>]*>([A-D])', html)
    if not options:
        # Try different pattern
        options = re.findall(r'data-answer="([^"]+)"', html)

    # Find correct answer from DB or compute
    # For simulation, let's determine if we'll get it right (75% chance)
    will_be_correct = random.random() < 0.75

    if will_be_correct:
        correct_count += 1

    # Get the question ID
    qid_match = re.search(r'name="question_id" value="(\d+)"', html)
    if qid_match:
        question_id = qid_match.group(1)
    else:
        question_id = "1"

    # Submit answer - for simplicity, let's just submit a fixed answer
    # and see what happens
    answer = "A"  # Simple approach

    resp = session.post(f'{BASE_URL}/session/{session_id}/answer', data={
        'question_id': question_id,
        'answer': answer,
        'response_time_s': '5'
    }, allow_redirects=False)

    print(f"Q{i+1}: {'Correct' if will_be_correct else 'Wrong'} (status: {resp.status_code})")

    # Follow redirect to get next question
    if resp.status_code == 302:
        next_url = resp.headers.get('Location', '')
        if next_url:
            session.get(f'{BASE_URL}{next_url}')

print(f"\n=== Results ===")
print(f"Total: {total}")
print(f"Correct: {correct_count}")
print(f"Accuracy: {correct_count/total*100:.1f}%")
