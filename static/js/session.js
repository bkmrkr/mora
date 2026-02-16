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

            // Visually disable buttons — do NOT set btn.disabled=true because
            // that strips the clicked button's value from the form data.
            // The CSS class uses pointer-events:none to block further clicks.
            document.querySelectorAll('.choice-btn').forEach(function(btn) {
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


});
