// Track response time
const startTime = Date.now();

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('answer-form');
    const timeField = document.getElementById('response_time_s');

    if (form && timeField) {
        form.addEventListener('submit', function() {
            const elapsed = (Date.now() - startTime) / 1000;
            timeField.value = elapsed.toFixed(1);
        });

        // Also update for MCQ button clicks
        document.querySelectorAll('.choice-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const elapsed = (Date.now() - startTime) / 1000;
                timeField.value = elapsed.toFixed(1);
            });
        });
    }

    // Keyboard shortcuts for MCQ
    document.addEventListener('keydown', function(e) {
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
});
