"""Test script to simulate a student answering questions."""
import requests
import random

BASE_URL = 'http://localhost:5002'

def main():
    # Create a new test student
    print("Creating test student...")
    resp = requests.post(f'{BASE_URL}/onboard', data={
        'student_name': 'TestStudent',
        'topic_name': '1st Grade Math'
    })
    print(f"Onboard response: {resp.status_code}")

    # Get student ID from response - follow redirect
    resp = requests.post(f'{BASE_URL}/onboard', data={
        'student_name': 'TestStudent2',
        'topic_name': '1st Grade Math'
    }, allow_redirects=False)
    if resp.status_code == 302:
        # Extract student ID from the redirect URL
        location = resp.headers.get('Location', '')
        print(f"Redirect to: {location}")

    # Let's just use student 1 which likely exists
    student_id = 1
    topic_id = 1

    print(f"\nStarting session for student {student_id}, topic {topic_id}...")

    # Start a session
    resp = requests.post(f'{BASE_URL}/session/start', data={
        'student_id': str(student_id),
        'topic_id': str(topic_id)
    }, allow_redirects=False)

    if resp.status_code == 302:
        session_id = resp.headers.get('Location', '').split('/')[-2]
        print(f"Session started: {session_id}")
    else:
        print(f"Failed to start session: {resp.status_code}")
        return

    # Track results
    correct = 0
    wrong = 0
    total = 20  # Run through 20 questions

    for i in range(total):
        # Get question
        resp = requests.get(f'{BASE_URL}/session/{session_id}/question')
        if resp.status_code != 200:
            print(f"Failed to get question: {resp.status_code}")
            break

        # Parse question from HTML - look for the data
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find question content
        question_div = soup.find('div', class_='question-content')
        if not question_div:
            print("Could not find question")
            break

        question_text = question_div.get_text(strip=True)[:100]
        print(f"\nQ{i+1}: {question_text}...")

        # Find options
        options = []
        for btn in soup.find_all('button', class_='choice-btn'):
            opt_text = btn.get_text(strip=True)
            options.append(opt_text)

        if not options:
            print("No options found - might be short answer")
            # Try to find the correct answer in a hidden field or data attribute
            continue

        # Determine if we should get this right (75% chance)
        get_correct = random.random() < 0.75

        if get_correct:
            # Find the correct answer
            correct += 1
            # Parse the answer - look for it in the page or generate
            # For now, just pick a random option and hope it includes the right one
            # Actually we need to find the correct answer from the question
            print(f"  -> Getting CORRECT (running total: {correct} correct, {wrong} wrong)")
            answer = options[0]  # This won't work - we need actual correct answer
        else:
            wrong += 1
            print(f"  -> Getting WRONG (running total: {correct} correct, {wrong} wrong)")
            # Pick a wrong answer
            answer = options[1] if len(options) > 1 else options[0]

        # Actually, let's just fetch the question properly
        break

    print(f"\nFinal: {correct} correct, {wrong} wrong")

if __name__ == '__main__':
    main()
