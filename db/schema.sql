CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS curriculum_nodes (
    id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    prerequisites TEXT DEFAULT '[]',
    mastery_threshold REAL DEFAULT 0.75
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    topic_id INTEGER REFERENCES topics(id),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    total_questions INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    curriculum_node_id INTEGER NOT NULL REFERENCES curriculum_nodes(id),
    content TEXT NOT NULL,
    question_type TEXT CHECK(question_type IN ('mcq', 'short_answer', 'problem')),
    options TEXT,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty REAL,
    estimated_p_correct REAL,
    generated_prompt TEXT,
    model_used TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    student_id INTEGER NOT NULL REFERENCES students(id),
    session_id TEXT REFERENCES sessions(id),
    answer_given TEXT,
    is_correct INTEGER NOT NULL,
    partial_score REAL DEFAULT NULL,
    response_time_seconds REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_skill (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    curriculum_node_id INTEGER NOT NULL REFERENCES curriculum_nodes(id),
    skill_rating REAL DEFAULT 800.0,
    uncertainty REAL DEFAULT 350.0,
    mastery_level REAL DEFAULT 0.0,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, curriculum_node_id)
);

CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON attempts(timestamp);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_student_skill_student ON student_skill(student_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_nodes_topic ON curriculum_nodes(topic_id);
