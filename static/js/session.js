// Track response time
const startTime = Date.now();
let submitted = false;

// --- Text-to-Speech for questions ---
function speakQuestion() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    var el = document.querySelector('.question-text');
    if (!el) return;

    // Get text and convert math symbols to spoken words
    var text = el.textContent.trim();
    text = text.replace(/\+/g, ' plus ')
               .replace(/\u2212/g, ' minus ')   // unicode minus
               .replace(/ - /g, ' minus ')
               .replace(/\u00d7/g, ' times ')    // ×
               .replace(/\u00f7/g, ' divided by ') // ÷
               .replace(/\*/g, ' times ')
               .replace(/=/g, ' equals ')
               .replace(/</g, ' is less than ')
               .replace(/>/g, ' is greater than ')
               .replace(/\?/g, '?')
               .replace(/\s+/g, ' ');

    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
}

document.addEventListener('DOMContentLoaded', function() {
    // Auto-speak the question on load
    speakQuestion();

    // Wire up replay button
    var speakBtn = document.getElementById('speak-btn');
    if (speakBtn) {
        speakBtn.addEventListener('click', function() { speakQuestion(); });
    }

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

    // Keyboard shortcuts for MCQ (A/B/C/D or 1/2/3/4)
    document.addEventListener('keydown', function(e) {
        if (submitted) return;
        var key = e.key.toUpperCase();
        // Map number keys to letter keys
        var numMap = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'};
        if (numMap[key]) key = numMap[key];
        if ('ABCD'.includes(key)) {
            var btn = document.querySelector('.choice-btn[data-key="' + key + '"]');
            if (btn) {
                btn.click();
            }
        }
    });


});
