**Moriah: Specification for an Adaptive, LLM-Powered Learning Program**

Moriah is a local, privacy-first adaptive learning system. It starts from any user-specified topic (e.g., "Calculus", "Python for Data Science", "World War II History") and dynamically generates questions using a local Ollama model. The system keeps the student in their "sweet spot" by targeting an ~80% success rate per question, inspired by ELO rating systems (widely used in adaptive education) with Bayesian elements for robust skill estimation. It respects a structured curriculum, adjusts progression based on performance, and heavily weights the most recent 30 questions when deciding the next one. All questions, attempts, and progress statistics are stored persistently in SQLite.

### Core Goals
- **Optimal Challenge Zone**: Target ~80% correctness probability to maximize learning (neither too easy nor too frustrating).
- **Adaptive Difficulty**: Increase difficulty after correct answers; decrease after incorrect ones.
- **Curriculum-Aware**: Follow a hierarchical structure of topics/subtopics/concepts while allowing dynamic adjustments (e.g., revisit prerequisites if struggling).
- **Recent-History Driven**: The next question is primarily derived from analysis of the previous 30 interactions (accuracy, topic coverage, trends).
- **Local & Extensible**: Runs entirely offline with Ollama + SQLite. Easy to extend with new models or UIs.

### High-Level Architecture
- **Frontend**: Web-based (recommended: Streamlit or Gradio for quick interactive sessions) or simple CLI/TUI. Features a dashboard for progress, session controls, and topic selection.
- **Backend**: Python (3.10+). Libraries: `ollama` (or `openai`-compatible client), `sqlite3`/`SQLAlchemy`, `pandas` (for quick stats on recent attempts).
- **LLM Integration**: Ollama (local models like Llama 3.1/3.2, Gemma 2, Phi-3, or Mistral variants—choose based on hardware for speed vs. quality).
- **Storage**: Single SQLite file (`moriah.db`) for portability and privacy.
- **Session Flow**: Interactive loop—generate question → present → evaluate answer → provide feedback & explanation → update model → repeat.

### Data Model (SQLite Schema)

Here's a practical, normalized schema. It supports multiple students/topics, hierarchical curricula, dynamic questions, and rich progress tracking.

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,          -- e.g., "Calculus"
    description TEXT,
    parent_id INTEGER REFERENCES topics(id)  -- for hierarchies
);

CREATE TABLE curriculum_nodes (         -- subtopics/concepts, e.g., "Derivatives", "Chain Rule"
    id INTEGER PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id),
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER,                -- suggested sequence
    prerequisites TEXT,                 -- JSON array of node IDs or comma-separated
    mastery_threshold REAL DEFAULT 0.75 -- e.g., 75% recent accuracy + skill rating
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    curriculum_node_id INTEGER REFERENCES curriculum_nodes(id),
    content TEXT NOT NULL,
    question_type TEXT CHECK(question_type IN ('mcq', 'short_answer', 'problem')),
    options TEXT,                       -- JSON array for MCQ
    correct_answer TEXT NOT NULL,
    difficulty REAL,                    -- 0.0-1.0 normalized or ELO-scale value
    estimated_p_correct REAL,           -- model's/target probability (aim ~0.8)
    generated_prompt TEXT,              -- store for debugging/reproducibility
    model_used TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attempts (
    id INTEGER PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    student_id INTEGER REFERENCES students(id),
    answer_given TEXT,
    is_correct BOOLEAN NOT NULL,
    partial_score REAL DEFAULT NULL,    -- 0-1 for open-ended
    response_time_seconds INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_skill (
    id INTEGER PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    curriculum_node_id INTEGER REFERENCES curriculum_nodes(id),
    skill_rating REAL DEFAULT 1000.0,   -- ELO-style (higher = stronger)
    uncertainty REAL DEFAULT 300.0,     -- Bayesian-like variance/uncertainty
    mastery_level REAL DEFAULT 0.0,     -- 0.0-1.0 computed score
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, curriculum_node_id)
);

-- Indexes for performance on recent queries
CREATE INDEX idx_attempts_timestamp ON attempts(timestamp);
CREATE INDEX idx_attempts_student ON attempts(student_id);
```

**Key Queries**:
- Last 30 questions: `SELECT * FROM attempts WHERE student_id = ? ORDER BY timestamp DESC LIMIT 30;`
- Recent accuracy: Aggregate `is_correct` and join with `questions` for node/difficulty.
- Current skill: Read from `student_skill`.

### Adaptive Algorithm (ELO-like + Bayesian Elements)

**Skill Model**:
- Maintain a continuous **skill_rating** (ELO-inspired, starting ~1000) per curriculum node.
- Add **uncertainty** (starts high, decreases with more data) for a lightweight Bayesian flavor—similar to TrueSkill or simple Gaussian updates.
- Optional hybrid with Bayesian Knowledge Tracing (BKT) elements for discrete "mastered" state per node (probability of knowing the concept, with learn/slip/guess parameters).

**Targeting 80% Success**:
- When generating a question, compute **target_difficulty** ≈ current_skill_rating adjusted for recent performance.
- Use a logistic (sigmoid) function for probability:  
  P(correct) ≈ 1 / (1 + 10^((D - S) / 400))  
  Solve for D such that P ≈ 0.8 (D will be somewhat easier than S).
- If recent 30-question accuracy > 80% → increase target difficulty (or reduce offset).  
  If < 80% → decrease difficulty.  
  This creates a feedback loop that self-calibrates.

**Update Rules** (after each attempt):
- Compute expected P (target was 0.8, or based on assigned D).
- ELO-style update:  
  `delta = K * (actual - expected)`  
  (K = dynamic factor, e.g., 32 base, higher for early attempts, lower later; scale by uncertainty).
- Correct → skill_rating increases; Wrong → decreases.
- Reduce uncertainty with more data (e.g., uncertainty /= sqrt(1 + attempts)).
- Update mastery_level = skill_rating normalized + recent accuracy weight.
- If mastery_level > threshold on current node → advance in curriculum (unlock next nodes). If low → insert prerequisite review questions.

**Next Question Logic** (heavily based on previous 30):
1. Query last 30 attempts + associated questions/nodes.
2. Compute: overall accuracy, accuracy by node, average difficulty faced, improvement trend (e.g., rolling average).
3. Decide focus node: Current or next in curriculum; fallback to prerequisites if recent accuracy low on current.
4. Compute target difficulty from current skill + recent performance adjustment.
5. Generate question via Ollama at that target.

**Curriculum Adjustment**:
- Start with a high-level outline (predefined for common topics or LLM-generated on first run: "Create a hierarchical curriculum for [topic] with 8-12 nodes").
- Progress linearly but adapt: accelerate on mastery, remediate on weakness.
- Track coverage to avoid over-focusing on one area.

### Question Generation & Evaluation

**Ollama Prompt Template** (example—refine iteratively):

```
You are an expert tutor creating adaptive questions for a student learning [topic].

Current focus: [curriculum_node name + description]
Student skill level: [skill_rating description, e.g., "solid intermediate"]
Recent performance (last 30 questions): [summary: 78% accuracy, strong on basics, weaker on applications]
Target: Generate a question with ~80% chance of correct answer for this student.

Question type: [mcq / short_answer / problem-solving]
Output strictly as JSON:
{
  "question": "...",
  "options": ["A", "B", "C", "D"] (if mcq),
  "correct_answer": "...",
  "explanation": "Detailed step-by-step solution and why it's correct",
  "estimated_difficulty": 0.XX (0.0-1.0),
  "tags": ["concept1", "concept2"]
}
```

- Call Ollama (temperature ~0.7 for creativity, but structured output via JSON mode or guided prompting).
- Store the full prompt and response for reproducibility.
- For open-ended answers: Second Ollama call to grade ("Compare student answer to correct answer and rubric. Output score 0/1 and feedback.").

**Question Variety**: Support MCQ (easiest to auto-grade), short answer, and worked problems. Prefer MCQ initially for reliability.

**Feedback**: After answer, show correct answer + LLM-generated explanation. Celebrate wins, encourage on misses.

### User Flow
1. **Onboarding**: Student name + topic input. System loads/creates curriculum.
2. **Session Start**: Review progress dashboard (skill curves, mastery map, last 30 stats).
3. **Learning Loop**:
   - System analyzes recent history → selects node & target difficulty.
   - Generates question.
   - Student answers (text input or choices).
   - Immediate feedback + update DB.
   - Repeat (10-20 questions per session recommended).
4. **Session End**: Summary report, suggestions for next focus.
5. **Progress Tracking**: Visuals (charts via Matplotlib/Plotly in UI), exportable stats.

### Technical & Implementation Considerations
- **Offline-First**: Everything local. Recommend 8+ GB RAM for comfortable Ollama performance.
- **Performance**: Cache recent stats; limit heavy queries.
- **Edge Cases**: New topics (start easy), cold starts (low data → conservative difficulty), very long sessions (cap history weighting).
- **Extensibility**: Configurable target success rate (default 80%), preferred question types, model selection.
- **Testing**: Seed with sample data; simulate student answers to tune K-factor and offsets.
- **Security/Privacy**: No network calls except optional Ollama (local).

This specification provides a solid, implementable foundation. You can start with a minimal CLI prototype (SQLite + Ollama loop) and expand to a nice web UI. The combination of ELO-style updates, recent-history analysis, curriculum structure, and dynamic LLM generation makes Moriah powerful yet straightforward to build.

If you'd like me to expand any section (full sample code snippets, detailed prompt engineering, UI wireframes, or refinements), just let me know!