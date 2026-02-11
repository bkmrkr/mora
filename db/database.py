"""SQLite database connection helper and initialization."""
import logging
import os
import sqlite3

from config.settings import DB_PATH

log = logging.getLogger(__name__)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    try:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
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
