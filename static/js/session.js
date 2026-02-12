// Track response time
const startTime = Date.now();
let submitted = false;

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('answer-form');
    const timeField = document.getElementById('response_time_s');

    if (form && timeField) {
        form.addEventListener('submit', function(e) {
            // Prevent double-submit: if already submitted, block the second POST
            if (submitted) {
                e.preventDefault();
                return;
            }
            submitted = true;

            const elapsed = (Date.now() - startTime) / 1000;
            timeField.value = elapsed.toFixed(1);

            // Disable all choice buttons to prevent further clicks
            document.querySelectorAll('.choice-btn').forEach(function(btn) {
                btn.disabled = true;
                btn.classList.add('submitting');
            });
        });

        // Also update time for MCQ button clicks
        document.querySelectorAll('.choice-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const elapsed = (Date.now() - startTime) / 1000;
                timeField.value = elapsed.toFixed(1);
            });
        });
    }

    // Keyboard shortcuts for MCQ
    document.addEventListener('keydown', function(e) {
        if (submitted) return;  // Ignore after submission
        const key = e.key.toUpperCase();
        if ('ABCD'.includes(key)) {
            const btn = document.querySelector('.choice-btn[data-key="' + key + '"]');
            if (btn) {
                btn.click();
            }
        }
    });

    // Auto-focus text input
    const input = document.getElementById('answer-input');
    if (input) {
        input.focus();
    }

    // Pre-cache next question while student thinks
    if (form) {
        const action = form.getAttribute('action') || '';
        const match = action.match(/\/session\/([^/]+)\/answer/);
        if (match) {
            const sessionId = match[1];
            fetch('/session/' + sessionId + '/precache', {method: 'POST'})
                .catch(function() {}); // fire-and-forget
        }
    }
});
