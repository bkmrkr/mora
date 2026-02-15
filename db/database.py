"""SQLite database connection helper and initialization."""
import logging
import os
import sqlite3

from config.settings import DB_PATH

log = logging.getLogger(__name__)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def _migrate(conn):
    """Add columns to existing tables (safe to run repeatedly)."""
    migrations = [
        ('sessions', 'current_question_id', 'INTEGER REFERENCES questions(id)'),
        ('sessions', 'last_result_json', 'TEXT'),
        ('attempts', 'curriculum_node_id', 'INTEGER REFERENCES curriculum_nodes(id)'),
        ('attempts', 'skill_rating_before', 'REAL'),
        ('attempts', 'skill_rating_after', 'REAL'),
        ('questions', 'test_status', "TEXT DEFAULT 'approved' CHECK(test_status IN ('pending_review', 'approved', 'rejected'))"),
        ('questions', 'validation_error', 'TEXT'),
    ]
    for table, column, col_type in migrations:
        if not _column_exists(conn, table, column):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            log.info("Migration: added %s.%s", table, column)
    conn.commit()


def init_db():
    conn = get_db()
    try:
        # Read schema and split into statements
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        # Run migrations before indexes (existing DBs need new columns first)
        # Execute CREATE TABLE statements first
        for stmt in schema.split(';'):
            stmt = stmt.strip()
            if not stmt:
                continue
            if stmt.upper().startswith('CREATE TABLE'):
                conn.execute(stmt)
        conn.commit()
        _migrate(conn)
        # Now execute remaining statements (CREATE INDEX, etc.)
        for stmt in schema.split(';'):
            stmt = stmt.strip()
            if not stmt:
                continue
            if not stmt.upper().startswith('CREATE TABLE'):
                conn.execute(stmt)
        conn.commit()
        log.info("Database initialized at %s", DB_PATH)
    finally:
        conn.close()


def query_db(sql, params=(), one=False):
    conn = get_db()
    try:
        cur = conn.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]
        return rows[0] if (one and rows) else (None if one else rows)
    except sqlite3.Error as e:
        log.error("query_db error: %s | SQL: %s", e, sql[:200])
        raise
    finally:
        conn.close()


def execute_db(sql, params=()):
    conn = get_db()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        log.error("execute_db error: %s | SQL: %s", e, sql[:200])
        raise
    finally:
        conn.close()
