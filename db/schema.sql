-- Mora v2: Math-only adaptive learning
-- 5 tables (simplified from v1's 8)

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_progress (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    skill_id TEXT NOT NULL,
    skill_rating REAL DEFAULT 800.0,
    uncertainty REAL DEFAULT 350.0,
    mastery_level REAL DEFAULT 0.0,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, skill_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    total_questions INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    current_question_id INTEGER REFERENCES questions(id),
    last_result_json TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    skill_id TEXT NOT NULL,
    content TEXT NOT NULL,
    question_type TEXT CHECK(question_type IN ('mcq', 'short_answer')),
    options TEXT,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty REAL,
    template_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id TEXT REFERENCES sessions(id),
    skill_id TEXT NOT NULL,
    answer_given TEXT,
    is_correct INTEGER NOT NULL,
    response_time_seconds REAL,
    skill_rating_before REAL,
    skill_rating_after REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_progress_student ON student_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_progress_skill ON student_progress(student_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_questions_skill ON questions(skill_id);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_skill ON attempts(skill_id);
CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON attempts(timestamp);
