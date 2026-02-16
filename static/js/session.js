// Track response time
const startTime = Date.now();
let submitted = false;

// --- Text-to-Speech ---
var ttsEnabled = localStorage.getItem('mora_tts') !== 'off';
var preferredVoice = null;

// Pick a warm, slightly accented voice when available
function pickVoice() {
    if (!window.speechSynthesis) return;
    var voices = speechSynthesis.getVoices();
    if (!voices.length) return;
    // Prefer: Carmit (Hebrew-accented), Tessa (South African), Daniel (British)
    var prefs = ['carmit', 'tessa', 'daniel', 'moira', 'karen'];
    for (var i = 0; i < prefs.length; i++) {
        for (var j = 0; j < voices.length; j++) {
            if (voices[j].name.toLowerCase().indexOf(prefs[i]) !== -1) {
                preferredVoice = voices[j];
                return;
            }
        }
    }
    // Fallback: first English voice
    for (var k = 0; k < voices.length; k++) {
        if (voices[k].lang.startsWith('en')) { preferredVoice = voices[k]; return; }
    }
}

function speak(text) {
    if (!window.speechSynthesis || !ttsEnabled) return;
    window.speechSynthesis.cancel();
    var utterance = new SpeechSynthesisUtterance(text);
    if (preferredVoice) utterance.voice = preferredVoice;
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    window.speechSynthesis.speak(utterance);
}

function mathToWords(text) {
    return text.replace(/\+/g, ' plus ')
               .replace(/\u2212/g, ' minus ')
               .replace(/ - /g, ' minus ')
               .replace(/\u00d7/g, ' times ')
               .replace(/\u00f7/g, ' divided by ')
               .replace(/\*/g, ' times ')
               .replace(/=/g, ' equals ')
               .replace(/</g, ' is less than ')
               .replace(/>/g, ' is greater than ')
               .replace(/\?/g, '?')
               .replace(/\s+/g, ' ');
}

function speakQuestion() {
    var el = document.querySelector('.question-text');
    if (!el) return;
    speak(mathToWords(el.textContent.trim()));
}

function speakFeedback() {
    // Correct answer banner on question page
    var correct = document.querySelector('.result-banner.correct');
    if (correct) {
        speak(correct.textContent.trim().split('\n')[0]);
        return;
    }
    // Wrong answer feedback page
    var wrongHeader = document.querySelector('.feedback-card.wrong h2');
    if (wrongHeader) {
        var correctAnswer = document.querySelector('.correct-text');
        var msg = wrongHeader.textContent.trim();
        if (correctAnswer) msg += '. The answer is ' + mathToWords(correctAnswer.textContent.trim());
        var explanation = document.querySelector('.explanation-box p');
        if (explanation) msg += '. ' + mathToWords(explanation.textContent.trim());
        speak(msg);
    }
}

function updateVolumeBtn() {
    var btn = document.getElementById('volume-btn');
    if (!btn) return;
    btn.innerHTML = ttsEnabled ? '&#128264;' : '&#128263;';
    btn.title = ttsEnabled ? 'Sound on — click to mute' : 'Sound off — click to unmute';
    btn.classList.toggle('muted', !ttsEnabled);
}

document.addEventListener('DOMContentLoaded', function() {
    // Load voices (async on some browsers)
    pickVoice();
    if (window.speechSynthesis) {
        speechSynthesis.onvoiceschanged = pickVoice;
    }

    updateVolumeBtn();

    // Auto-speak: question page → read question; feedback page → read feedback
    if (ttsEnabled) {
        if (document.querySelector('.question-text')) {
            speakQuestion();
        } else if (document.querySelector('.feedback-card')) {
            speakFeedback();
        }
    }

    // Volume toggle
    var volumeBtn = document.getElementById('volume-btn');
    if (volumeBtn) {
        volumeBtn.addEventListener('click', function() {
            ttsEnabled = !ttsEnabled;
            localStorage.setItem('mora_tts', ttsEnabled ? 'on' : 'off');
            updateVolumeBtn();
            if (ttsEnabled) {
                speakQuestion();
            } else {
                window.speechSynthesis && window.speechSynthesis.cancel();
            }
        });
    }

    // Replay button
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
