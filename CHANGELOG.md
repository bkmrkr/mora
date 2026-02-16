# Mora v2 Changelog

### Added — Session-to-session skill comparison ("You vs Last Time")
- End-of-session summary compares accuracy per skill against the previous session
- Shows green ▲ for improved skills, red ▼ for declined skills (e.g., "40% → 80% ▲")
- Only appears when there's skill overlap between sessions
- Connects practice sessions into a visible learning arc

### Added — Mistake pattern analysis on wrong answers
- Analyzes the student's wrong answer vs correct answer to identify what went wrong
- Detects off-by-1 (counting error), off-by-10/100 (place value), swapped digits, wrong operation
- Shows a blue lightbulb hint above the explanation: e.g., "Off by 10 — check your tens place"
- Three layers of feedback: mistake hint → explanation → skill tip
- Only triggers for numeric answers where a pattern is detected

### Added — Skill momentum indicator on question card
- Green ▲ arrow when recent accuracy is improving on a skill ("rising")
- Red ▼ arrow when recent accuracy is declining ("falling")
- Compares recent half vs older half of last 6 attempts per skill
- Only shows after 4+ attempts on the skill (enough data for trend)
- Helps students see direction of progress, not just current mastery level

### Added — Immediate retry after wrong answers
- After getting a question wrong, ~50% chance the next question targets the same skill
- Different question/template, but same skill — immediate retrieval practice
- Research-backed: spaced retrieval on failed items accelerates learning
- Wired through `retry_skill_id` parameter in question generation pipeline

### Added — Curriculum preview on home page
- "40 skills across 4 grades" section below the start form
- Shows key topics per grade: addition/subtraction (1), regrouping/multiplication (2), etc.
- Gives new students a clear picture of the learning journey ahead

### Added — Math Level badge visible during practice sessions
- Student's Math Level (e.g., "Grandmaster") shown as a purple pill badge in the session header
- Makes the gamification visible during actual practice, not just on the dashboard
- Level computed at session start and stored in flask_session

### Improved — Dashboard index with level names and "Today" badges
- Each student card now shows their Math Level name (Starter, Grandmaster, etc.)
- Green "Today" badge appears next to students who practiced today
- Parents/teachers can see at a glance who practiced and their progress level

### Added — Math Level system on dashboard
- Gamified leveling: Starter → Explorer → Learner → Scholar → Expert → Champion → Master → Grandmaster → Legend
- Each level requires 5 more mastered skills (40 total = Legend)
- Purple gradient hero card at top of dashboard shows current level
- Gold progress bar shows advancement toward next level
- "N more to next level" hint keeps students motivated

### Added — Dashboard practice summary with accuracy trend chart
- Practice Summary section with total questions, overall accuracy, and session count
- Visual bar chart showing accuracy per session (last 10), color-coded by performance
- Green bars for 80%+ accuracy, amber for 60-79%, red for below 60%
- Gives students and parents a clear view of learning trajectory over time

### Added — Struggle detection with warm encouragement
- Tracks consecutive wrong answers during a session
- After 3+ wrong in a row, shows a warm encouragement message with amber styling
- "Tough stretch — that's okay! Hard problems mean you're learning new things."
- Resets when the student gets a correct answer
- Replaces the standard encouragement to acknowledge difficulty without discouragement

### Added — Spaced review for mastered skills
- ~20% of questions now review mastered skills for long-term retention
- Review questions prioritize skills not practiced recently (stalest first)
- Purple "Review" badge shown on review questions instead of difficulty label
- Prevents the forgetting curve — mastered skills stay sharp with periodic practice
- 5 new tests for review selection logic

### Added — Unlock progress indicators on dashboard
- Locked skills with multiple prerequisites now show a yellow progress bar
- "N/M unlocked" count shows how many prerequisites are already mastered
- Helps students see they're making progress even on skills they can't attempt yet
- Only appears for skills with 2+ prerequisites (single-prereq skills just show the name)

### Improved — Personalized session summary messages
- Summary headline adapts to performance: "Outstanding!" (90%+), "Great Session!" (70%+), "Good Effort!" (50%+), or encouraging message
- Subtitle personalized with student name and performance-appropriate phrasing
- Session insight highlights best skill or skill needing work (e.g., "Perfect on Place Value!")
- Makes the summary feel like a personal coach reviewing each session

### Added — Focus skill card with "Practice Now" on dashboard
- Dashboard overview now shows "Next Focus" card with the skill closest to mastery
- Prominent "Practice Now" button starts a new session directly from the dashboard
- Practice streak badge shown next to mastery count when streak is 2+ days
- Closes the loop between reviewing progress and taking action

### Improved — Mobile-responsive layout
- Answer buttons stack to single column on mobile (full-width touch targets)
- Stat cards, grade overview, skill grid all reflow for small screens
- Summary action buttons go full-width on mobile
- Tested at 375px (iPhone SE) — all pages usable on phones and tablets

### Added — Skill-specific learning tips on wrong answers
- Each of the 40 skills now has a pedagogical tip (e.g., "Make a ten first, then add what's left")
- Tips shown on feedback page between explanation and encouragement
- Blue accent bar distinguishes tips from other feedback elements
- Turns each mistake into a teaching moment with actionable strategy

### Added — Visible skill rating changes
- Correct answers show green "+N" badge on the result banner (e.g., "+6.6")
- Wrong answers show red "-N" badge next to skill rating on feedback page
- Makes the adaptive ELO engine tangible — students see harder questions are worth more
- Rating change computed from before/after skill ratings already tracked in answer service

### Added — Daily practice streak tracking
- Computes consecutive days of practice from session history (no schema change)
- Welcome banner shows "N day streak!" badge for streaks of 2+ days
- Session summary shows Day Streak stat card
- Encourages daily practice — the consistent repetition that makes ELO-based learning effective

### Added — Answer timeline on session summary
- Visual dot timeline showing correct (green) and wrong (red outlined) answers in order
- Hover tooltips show question number and result (e.g., "Q3: Wrong")
- Students see their learning trajectory at a glance — patterns of improvement become visible
- Placed between stat cards and skills list for natural reading flow

### Added — Session goal with progress tracking
- Each session starts with a goal of 10 questions
- Progress bar and counter (e.g., "3/10") shown in session header
- Bar fills as questions are answered, turns green when goal is reached
- One-time celebration banner when goal is hit: "Goal reached! 10 questions done!"
- Students can keep going past the goal — no forced stop
- Gives young learners a clear, achievable target each session

### Improved — Per-skill session accuracy on session summary
- Session summary now shows how many questions each skill got right (e.g., "3/4")
- Color-coded accuracy badges: green (≥80%), yellow (≥50%), red (<50%)
- Replaces simple skill list with actionable per-skill breakdown
- Students see exactly which skills need more practice

### Added — Mastery count badges on home page student chips
- Returning student buttons now show "N/40" mastery badge (e.g., "Sophia 36/40")
- Only shown when student has at least 1 mastered skill
- Purple pill badge inside chip button, fades on hover
- Progress visible at a glance before starting a session

### Improved — Dashboard student cards with grade level and progress bar
- Student cards now show current grade level badge (e.g., "Grade 4")
- Overall mastery progress bar (X/40 skills) on each card
- Current grade determined by highest grade with active practice
- Gives parents instant snapshot of each child's progress

### Added — Focus skill recommendation on session summary
- After ending a session, show "Next Focus" card with the skill closest to mastery
- Only recommends unlocked skills (prerequisites met)
- Shows skill name, grade, and current mastery percentage
- Makes the adaptive engine a collaborator — students know where to focus next

### Added — Grade progress overview bar on dashboard
- Summary bar at top of student dashboard: "N/40 skills mastered"
- Four progress bars showing per-grade completion (e.g., "Grade 2: 10/10")
- Completed grades shown in green, active grades in purple
- Gives instant big-picture view before scrolling into per-skill details

### Added — Prerequisite skill tree on dashboard
- Dashboard skill cards now show lock/unlock/mastered status
- Locked skills display lock icon and "Needs: ..." with prerequisite names
- Mastered skills show green checkmark
- Locked cards are faded (opacity 0.6) to visually distinguish from active skills
- Makes the adaptive prerequisite DAG visible — students see their learning path
- Fixed edge case: mastered skills with unmastered prerequisites don't show as locked

### Improved — Encouraging feedback on wrong answers
- Context-aware encouragement messages based on current mastery level
- "Almost there!" for skills near mastery (50%+), "Making progress!" for 25%+, "Every mistake helps you learn" for new skills
- "So close!" header with eyes emoji when the answer was close to correct (via `is_close` flag)
- Green encouragement bar between explanation and skill info — warm tone for young learners

### Added — Speed feedback and average response time
- "Lightning!" badge on correct answers under 3 seconds, "Quick!" under 6 seconds
- Speed badge appears as a pill on the green correct banner
- Average response time stat card on session summary page
- Rewards fluency and confidence — not just accuracy

### Added — Difficulty indicator and personalized welcome
- Show difficulty label on each question: Warm-up / On track / Stretch / Challenge
- Label is computed from the gap between question difficulty and student's skill rating
- Makes the adaptive engine visible — students see that questions adjust to their level
- Personalized "Welcome back!" banner when returning students start a new session
- Shows grade-by-grade progress pills (e.g., "G1: 4/10") with color coding
- Welcome banner shown once on the first question, then auto-dismissed

### Added — Skill unlock notifications
- When a student masters a skill, check if any new skills are now unlocked (all prerequisites met)
- Show blue "Unlocked: Skill Name (Grade N)" banner on the next question
- Traverses the prerequisite DAG to find newly eligible skills
- Only shows skills that aren't already mastered

### Added — Skill progress bar on question page
- Show real-time mastery progress bar below the skill name on every question
- Displays current mastery percentage and grade level (e.g., "Grade 1")
- Bar turns green when skill is mastered (>= 65%)
- Makes every correct answer feel meaningful — progress is visible in real-time

### Added — Skill mastery and grade completion celebrations
- Detect when a student masters a skill (crosses 0.65 threshold) during a session
- Show animated golden "Skill Mastered!" banner with spinning star on the next question
- Detect when all 10 skills in a grade become mastered (grade completion)
- Show special purple "Grade N Complete!" celebration with trophy for grade milestones
- Both celebrations use CSS scale-in and glow animations for a satisfying moment

### Added — Streak tracking and encouragement
- Track consecutive correct answers during a session
- Streak banner with escalating messages: "Correct!" (1-2), "Nice streak! N in a row!" (3-4), "Amazing!" (5-6), "On fire!" (7-9), "Unstoppable!" (10+)
- Animated streak banner with gradient background and pulse glow for streaks of 3+
- Broken streak encouragement on feedback page: "Good effort — you had N in a row!"
- Best streak stat card on session summary page (shown for streaks of 2+)

### Fixed — Dashboard table clipped on small screens
- Session history table on dashboard was clipped at 320px viewport (accuracy column cut off)
- Added `overflow-x: auto` wrapper for horizontal scroll fallback
- Added `@media (max-width: 400px)` with tighter padding so table fits without scrolling on small phones

### Fixed — Abandoned Sessions Lose Stats
- When a student navigated away mid-session (clicked Home/Dashboard), the session's `total_questions` and `total_correct` stayed at 0 because they were only computed on explicit "End Session"
- Now: starting a new session auto-ends any open sessions for the same student, computing their totals from the `attempts` table
- Dashboard "Recent Sessions" table now correctly shows all sessions with question data, not just properly ended ones
- Fixed 28 existing abandoned sessions in the database

### Improved — Template Question Variety
- `g4_geometry`: expanded low-difficulty variants from 2 to 7 (was just "Parallel lines are..." / "Perpendicular lines are..." repeating verbatim — now includes real-world examples, identification, and angle questions)
- `g4_angles`: expanded low-difficulty from 3 variants to 9+ (classify, identify example, and range-based questions — reduced max repetition from 38% to <15%)
- Fixed grammar: "an right angle" → "a right angle", "an straight angle" → "a straight angle"
- Added proper explanations to all geometry low-difficulty variants

### Changed — MCQ Only Mode
- Disabled short answer mode; all questions now use multiple choice
- Short answer can be re-enabled later by restoring the mastery threshold check

### Fixed — Skill Selector Variety and Geometry Data
- `selector.py`: when only 1-2 eligible skills remain, expand candidates to all skills so the same skill doesn't repeat every other question
- `selector.py`: all-mastered students now cycle through all skills with variety instead of stuck on one
- `selector.py`: added small random jitter to break deterministic alternation on tied scores
- `grade4.py`: square had 4 parallel side pairs (wrong) — corrected to 2

### Fixed — Skip Counting Numbers Exceeding 120
- `g1_counting`: skip counting by 10s could produce sequences up to 530 (e.g. "Count by 10s: 470, 480, 490, ?")
- Capped start value so all numbers in the sequence stay within 120
- 46% of skip counting questions were above grade level — now 0%

### Cleaned up — Move Local Imports to Module Level
- `grade4.py`: moved `from math import gcd, lcm` to top-level (was re-imported on every fraction_ops call)
- `home.py`: moved `from models import session` to top-level (was inside start() function)

### Fixed — Eliminate Zero-Result Subtraction and Two-Step Questions
- `g1_sub_10` and `g1_sub_20`: prevented n - n = 0 questions (e.g. "What is 6 - 6?")
- `g2_two_step`: prevented add_then_sub variant from producing zero (e.g. "gets 3 more, gives away 9" from 6)
- Subtraction results now always >= 1; "5 - 0" still valid (teaches subtracting zero)

### Fixed — Money Template Grammar
- `g2_money`: "How many cents are 5 pennys worth?" → "pennies" (correct plural)
- `g2_money`: "How many cents is ..." → "How many cents are ..." (consistent grammar)
- `g2_odd_even`: explanation "16 ÷ 2 = 8.0" → "16 ÷ 2 = 8" (remove unnecessary .0)

### Fixed — Elapsed Time Distractor Format Mismatch
- `g3_elapsed_time`: when answer was "2 hours", distractors showed "150 minutes" instead of "2 hours 30 minutes"
- Distractors now use `_fmt_elapsed()` helper to match answer format (hours+minutes vs minutes-only)

### Fixed — Fraction Subtraction Producing Zero
- `g4_fraction_ops`: subtracting equivalent fractions (e.g. 2/6 - 1/3) gave "0/1" as answer
- Now regenerates numerators when adjusted values are equal, ensuring non-zero result
- Simplified swap logic for subtraction (removed redundant double-recalculation)

### Fixed — Ordinal Suffix in Factors Template
- `g4_factors_multiples`: "What is the 3th multiple" → "What is the 3rd multiple"

### Fixed — Singular/Plural Grammar in Word Problems
- `g4_multi_step_word`: "If 1 apples are eaten" → "If 1 apple is eaten" (singular)
- `g4_multi_step_word`: "plus 1 loose ones" → "plus 1 loose one" (singular)
- `g4_multi_step_word`: "How many things does each team have" → rewrote divide_add variant with consistent "pencils" item instead of mixing students and balls
- `g1_word_problems`: minimum first operand raised to 2 — eliminates "Emma has 1 apples", "There are 1 birds"
- `common.py word_problem_frame`: "1 more birds land" → "1 more bird lands", "1 fly away" → "1 flies away"

### Fixed — Degenerate "0 + 0" and "0 - 0" Questions
- `addition_within_10`: first operand minimum changed from 0 to 1 — eliminates "What is 0 + 0?"
- `subtraction_within_10`: first operand minimum changed from 0 to 1 — eliminates "What is 0 - 0?"
- "5 + 0" and "3 - 0" still possible (valid: teaches adding/subtracting zero)

### Removed — Unused Python Imports
- `services/question_service.py`: removed `from engine import elo` (never used) and `SKILLS` from curriculum.skills import
- `curriculum/templates/grade2.py`: removed unused `word_problem_frame` from common import

### Fixed — Summary Page Overwrites ended_at on Refresh
- `end_session()` was called every time the summary page was visited, overwriting `ended_at` timestamp
- Added guard: only call `end_session()` if session not already ended
- Refreshing the summary page now preserves the original end timestamp

### Removed — Dead _get_skill_progress Function
- Removed unused `_get_skill_progress()` from `routes/session.py` — sidebar progress was a v1 feature
- Removed unused `get_for_student` import and `get_skills_for_grade` import

### Fixed — Missing Result Banner Styling
- `result-banner` class used in `question.html` had no CSS definition — "Correct!" notification was unstyled plain text
- Added `.result-banner` and `.result-banner.correct` styles: green background, bold green text, rounded corners
- Now provides clear visual feedback when a student answers correctly

### Improved — Move Inline Styles to CSS Classes
- Removed redundant inline `style=` from clock visual div — `.clock-visual` CSS class already had these properties
- Fixed `.clock-visual` margin: changed `margin-bottom: 1rem` to `margin: 1rem 0` to match original
- Replaced inline styles in `error.html` with `.error-content` CSS class
- Replaced inline styles in `retry.html` with `.retry-content` CSS class
- Only 2 dynamic inline styles remain (mastery bar widths — data-driven, must stay inline)

### Removed — Dead v1 CSS Cleanup
- Removed 323 lines of unused CSS (749 → 426 lines, 43% reduction)
- Removed: `.report-form`, `.report-btn`, `.report-question` (report feature)
- Removed: `.btn-topic`, `.topic-name`, `.topic-desc`, `.topic-chip`, `.topic-list` (topic selection)
- Removed: `img.math-inline`, `img.math-display`, `code.math-fallback` (LLM math rendering)
- Removed: `.two-panel-layout`, `.panel-left`, `.panel-right` (v1 two-panel layout)
- Removed: `.result-card`, `.result-correct`, `.result-wrong`, `.result-empty`, `.result-header`, `.result-icon`, `.result-label`, `.result-row`, `.result-key`, `.result-meta`, `.delta` (v1 result card)
- Removed: `.progress-card`, `.progress-node`, `.progress-node-header`, `.progress-node-name`, `.progress-node-pct` (v1 progress card)
- Removed: `.difficulty-display`, `.difficulty-dots`, `.difficulty-dot` (v1 difficulty display)
- Removed: `.diagram-visual`, `.topic-mastery-display`, `.session-stat`, `.end-btn-form`, `.session-top-bar`, `.choice-letter`, `.pagination`, `.row-correct`, `.row-wrong`, `.question-cell`, `.progress-text`, `.progress-bar`, `.progress-fill`, `.mastery-bar.small`, `.topic-start-form`, `.end-session-form`, `.encouragement`, `.original-question`, `.key-concept`, `.tip-box`, `.type-badge`, `.text-mastered`, `.onboard-card`

### Fixed — Student Chips Stacked Vertically
- Home page student chips displayed vertically instead of horizontally
- Added `.student-chips` CSS class with `display: flex; flex-wrap: wrap; gap: 0.5rem`
- Chips now display in a clean horizontal row that wraps on narrow screens

### Hardened — Tighten CSP img-src
- Removed `data:` from `img-src` — no data URIs used; clock SVG is inline markup
- Final CSP: `default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; script-src 'self'`

### Removed — Dead Code Cleanup
- Removed `strip_letter` template filter from `app.py` — v2 templates never produce letter prefixes
- Removed `{{ option | strip_letter }}` from `question.html` — replaced with `{{ option }}`
- Removed unused `re` import from `app.py`
- Removed `#answer-input` auto-focus from `session.js` — HTML `autofocus` attribute handles this

### Hardened — Tighten CSP script-src
- Removed `'unsafe-inline'` from `script-src` in Content-Security-Policy header
- No inline scripts exist — all JS loaded via external `session.js`
- `style-src 'unsafe-inline'` kept (needed for mastery bar widths, clock centering)
- Verified: keyboard shortcuts, response time tracking, and all JS features still work

### Fixed — NULL total_correct in Empty Sessions
- `end_session()` stored NULL instead of 0 for `total_correct` when session had no attempts
- SQL `SUM()` returns NULL for 0 rows — added `COALESCE(..., 0)` to handle this
- Dashboard now filters out 0-question sessions in the route (not just template)
- Prevents empty "Recent Sessions" table from showing for students with no answered questions

### Fixed — Case-Sensitive Student Name Matching
- Typing "sophia" created a new student instead of matching existing "Sophia"
- `get_by_name()` now uses `COLLATE NOCASE` for case-insensitive lookup
- Schema updated with `COLLATE NOCASE` on `students.name` for new databases
- Verified: XSS in name field safely escaped by Jinja2 auto-escaping

### Improved — Clock SVG Accessibility
- Added `role="img"` and `aria-label="Clock face"` to clock SVG element
- Screen readers now announce the clock image properly

### Fixed — Short Answer Mode Was Unreachable
- Short answer threshold (0.7) was higher than mastery threshold (0.65)
- Skills got mastered and excluded from the eligible pool before reaching 0.7
- Lowered short answer threshold to 0.5 — students type answers once they're getting ~50% right on a skill
- Verified in Playwright: text input renders, correct/wrong answers graded, feedback works

### Fixed — Dashboard Shows "No Students" for Invalid Student ID
- `/dashboard/999` rendered empty index template saying "No students yet"
- Now redirects to `/dashboard/` which shows the actual student list

### Added — Styled Error Pages (404/500)
- Created `templates/error.html` extending `base.html` — proper nav, "Go Home" button
- Error handler now renders template instead of Flask's bare default HTML
- 404 and 500 pages show consistent app styling

### Fixed — Ended Sessions Could Be Resumed via Direct URL
- Navigating to `/session/<ended_id>/question` would generate new questions for an ended session
- Added `ended_at` guard to question, answer, feedback, and next_question routes
- Ended sessions now redirect to the summary page

### Fixed — session.js Not Loaded, Keyboard Shortcuts Broken
- `session.js` was never included in `question.html` — only an inline script for response time existed
- Missing features: keyboard shortcuts (A/B/C/D), double-submit prevention, button disable on submit
- Added `data-key` attributes (A/B/C/D) to MCQ buttons in template
- Replaced inline script with `<script src="session.js">` to load all features
- Verified with Playwright: keyboard shortcuts, response time, and navigation all work

### Hardened — Cookie Validation Requires question_type
- Answer route and question route now require `question_type` in session cookie validation
- Previously, a tampered cookie missing `question_type` caused `KeyError` crash in `answer_service.py`
- Added to both `required_keys` checks in `routes/session.py`

### Fixed — Error Handler Swallowed HTTP Status Codes
- Catch-all `@app.errorhandler(Exception)` was converting 404 Not Found to 500 Internal Server Error
- Now re-raises `HTTPException` subclasses (404, 405, etc.) with their correct status codes
- Only non-HTTP exceptions return 500

### Fixed — Non-Numeric response_time_s Crashed Answer Route
- `float(request.form.get('response_time_s', 0))` crashed with `ValueError` on non-numeric input ('abc', '', etc.)
- Now wrapped in try/except, defaults to 0.0 on invalid input

### Hardened — NaN/Inf Guards in ELO Functions
- All ELO functions (p_correct, compute_k_factor, update_skill, compute_mastery) now guard against NaN/Inf inputs
- Corrupted data falls back to safe defaults (800.0 for ratings, initial values for uncertainty)
- NaN can never enter through normal operation paths — guards are purely defensive

### Fixed — Fraction Equivalence in Short Answer Mode
- `_to_number()` now parses fractions like "1/2" → 0.5, so "2/4" is accepted when answer is "1/2"
- Also handles fraction-to-decimal comparison ("3/4" matches "0.75")
- Handles division by zero safely ("5/0" returns None)

### Fixed — Mastery Progression Too Slow
- Mastery formula overweighted ELO rating (60%) vs actual accuracy (40%) — student with 100% accuracy after 31 questions still couldn't unlock Grade 2
- Changed mastery weights to 0.3 rating / 0.7 accuracy — accuracy-dominant for faster progression
- Lowered mastery threshold from 0.75 to 0.65 — 80% accuracy students (the target rate) can now progress
- Added `min_attempts=5` gate to prevent mastering a skill with 1-2 lucky answers
- Result: perfect student masters a skill in ~5 questions; 80% student masters in ~5-8; 70% student stays put

### Fixed — Template Content Bugs (found via stress testing)
- g1_shapes: "What shape has 4 sides?" accepted only square OR rectangle — now only asks about shapes with unique side counts (triangle=3, hexagon=6)
- g2_odd_even: "Which number is odd?" showed multiple odd numbers in options but only one was accepted — now generates exactly 1 correct + 3 opposite-parity options
- g3_data: "Most popular pet?" had 26% chance of tied values with only one accepted — now uses unique values (`random.sample`)
- g3_elapsed_time: Showed 24-hour format ("ends at 13:00") and confusing 12-hour wraparound ("starts at 10:00, ends at 2:00") — now limits start time so end never exceeds 12

## [2026-02-15] — v2 Rewrite: Math-Only, Template-Based

Complete rewrite from multi-subject LLM-based system to math-only template-based system.

### Why
LLM (qwen2.5) could not reliably produce grade-appropriate educational content. After 10 phases of pipeline rebuilding, the fundamental problem remained: misleveled questions, broken options, and unpredictable output. Template-based generation is correct by construction.

### Added — Phase 1: DB + Models + Curriculum
- New 5-table schema: students, student_progress, sessions, questions, attempts
- `curriculum/skills.py` — 40 math skills across grades 1-4 with prerequisite DAG
- `models/progress.py` — upsert-based skill progress tracking (replaces student_skill.py)
- 88 tests (models + curriculum structure + DAG validation)

### Added — Phase 2: ELO Engine + Skill Selector
- `engine/selector.py` — prerequisite-gated skill selection with variety, virgin bonus, warm-start
- Kept unchanged: `engine/elo.py`, `engine/difficulty.py`, `engine/answer_matching.py`
- 16 selector tests (104 total)

### Added — Phase 3: Grade 1 Templates
- `curriculum/templates/grade1.py` — 10 template functions (add/sub 10/20, place value, counting, comparing, time, shapes, word problems)
- `curriculum/templates/common.py` — distractor generation (off-by-one, wrong-operation patterns), option shuffling, word problem frames
- Difficulty-aware: templates scale parameters based on ELO (e.g., max_sum=7 at low ELO, 10 at high)
- 15 template tests (119 total)

### Added — Phase 4: Services
- `services/question_service.py` — select skill → pick template → generate → store (no LLM)
- `services/answer_service.py` — grade answer → ELO update → record attempt (no LLM grading)
- 9 service tests (128 total)

### Added — Phase 5: Routes + UI
- `app.py` — simplified (3 blueprints, no admin, no Ollama)
- `routes/home.py` — name entry + returning student chips → start session
- `routes/session.py` — question → answer → feedback (wrong only) → next → end summary
- `routes/dashboard.py` — grade-by-grade progression with per-skill mastery bars
- All templates rewritten for math-only flow
- `make_options()` deduplication fix — guaranteed 4 unique options even with small numbers
- 20 route tests (148 total)

### Added — Phase 6: Grades 2-4 Templates
- `curriculum/templates/grade2.py` — 10 templates (add/sub 100/1000, intro multiply, money, time, measurement, fractions intro, comparing 3-digit, two-step, odd/even)
- `curriculum/templates/grade3.py` — 10 templates (mult/div facts, multi-digit mult, area/perimeter, fraction compare/add/sub, rounding, word problems, elapsed time, data interpretation)
- `curriculum/templates/grade4.py` — 10 templates (2x2 mult, long division, fraction ops with unlike denom, decimal place value/add/sub, angles, geometry, factors/multiples, multi-step word, equivalent fractions)
- `make_options()` extended: fraction distractor padding and decimal distractor padding
- 31 new tests (179 total)

### Verified — Phase 8: Playwright Browser Testing
- Full flow walked in real browser: home → start → question → correct (skip feedback) → wrong → feedback → next → end → summary → dashboard
- All 11 checkpoints pass: home page, question rendering, correct answer flow, wrong answer flow, feedback page, session summary, dashboard overview, dashboard index, returning student chip, session stats, console errors (zero)
- Grade-by-grade dashboard shows all 40 skills with mastery bars and ELO ratings

### Added — Phase 7: Integration Test
- `tests/test_integration.py` — full 20-question student journey via Flask test client
- Verifies: session lifecycle, ELO rating updates, attempt persistence, skill variety, dashboard display, student persistence across sessions, feedback flow (correct skips, wrong shows), accuracy calculation, returning student chips
- All 40 skills verified: registered in service, every template produces valid 4-option MCQ
- 10 integration tests (189 total)

### Added — Clock SVG Visuals for Time Questions
- `common.py`: `generate_clock_svg(hour, minute)` renders analog clock face with hour/minute hands
- Ported from kidtutor project — circle, tick marks, numbers, hour hand (thick), minute hand (thin), center dot
- Grade 1 (`g1_time`) and Grade 2 (`g2_time`) templates now show clock image instead of text like "A clock shows 12 o'clock"
- Question text changed to "What time does this clock show?" — no more giving away the answer
- Clock params (`clock_hour`, `clock_minute`) stored in session cookie (8 bytes vs ~2KB SVG), SVG regenerated at render time
- Verified with Playwright: clock renders correctly in browser

### Added — Intrinsic Difficulty Scoring
- `common.py`: `estimate_difficulty(grade, complexity)` maps grade (1-4) + complexity (0.0-1.0) to ELO difficulty
- Grade bands: G1 500-750, G2 700-950, G3 900-1150, G4 1100-1350
- All 40 templates now return a `difficulty` field based on actual question parameters (operand size, number of steps, denominator size, etc.)
- `question_service.py` uses intrinsic difficulty instead of target difficulty for ELO calculations
- Result: "2 + 1" gets difficulty ~525, "7 × 8" gets ~962, "1/2 + 1/4" gets ~1242

### Fixed — Stale Session Cookie Bug
- `routes/home.py`: clear Flask session on `/start` to purge stale v1 cookies
- `routes/session.py`: validate `current_question` has required v2 fields (`skill_id`, `question_id`, `correct_answer`, `options`) before using; discard and regenerate if invalid
- `routes/session.py`: `answer()` route redirects to question page (not end page) if session data is invalid
- Root cause: browser retained v1 session cookie with `current_question` missing `skill_id` field, causing `KeyError` in `answer_service.py`
- Verified fix with Playwright: full flow (home → start → correct → wrong → feedback → next → end → summary → dashboard) works with zero errors

### Removed
- All `ai/` modules (question_generator, json_utils, explainer, answer_grader, local_generators)
- Admin blueprint and templates
- LLM-related DB columns (generated_prompt, model_used, test_status, validation_error, quality_flags)
- Tables: topics, curriculum_nodes, question_reports, skill_history
- Precache system, similarity dedup, question validator (templates are correct by construction)
- Ollama configuration and warm-up
- `render_math`, `render_md_bold` template filters
- `scripts/` directory (generate, validate, seed scripts)
- `services/onboarding_service.py`, `services/math_renderer.py`
- 23 v1 test files

---

## v1 History (2026-02-11 to 2026-02-15)

See git history for the full v1 changelog. Key milestones:
- Multi-subject adaptive learning (Math, Reading, Science, Social Studies, Hebrew)
- LLM-based question generation with qwen2.5 via Ollama
- 10 phases of pipeline rebuilding to fix 97.7% broken question rate
- Final state: 441 tests, 247 validated questions, but fundamentally unreliable LLM output
