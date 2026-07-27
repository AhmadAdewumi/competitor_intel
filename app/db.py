# app/db.py
# ============================================
# COMPETITORINTEL - Database Layer
# ============================================

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Database path relative to project root
DB_PATH = Path("data/competitor_intel.db")


def get_db():
    """Get database connection."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            search_terms TEXT,
            urls TEXT,
            schedule_frequency TEXT,
            schedule_time TEXT,
            schedule_day TEXT,
            schedule_interval INTEGER,
            email TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reports table - FIXED: added created_at
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            content TEXT,
            filepath TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Traces table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            topic_id INTEGER,
            step_number INTEGER,
            agent TEXT,
            action TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")


# ============================================
# TOPIC OPERATIONS
# ============================================

def get_all_topics() -> List[Dict[str, Any]]:
    """Get all enabled topics."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE enabled = 1 ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    topics = []
    for row in rows:
        topic = dict(row)
        topic['search_terms'] = json.loads(topic['search_terms']) if topic['search_terms'] else []
        topic['urls'] = json.loads(topic['urls']) if topic['urls'] else []
        topics.append(topic)
    return topics


def get_topic(topic_id: int) -> Optional[Dict[str, Any]]:
    """Get a single topic by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE id = ? AND enabled = 1", (topic_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        topic = dict(row)
        topic['search_terms'] = json.loads(topic['search_terms']) if topic['search_terms'] else []
        topic['urls'] = json.loads(topic['urls']) if topic['urls'] else []
        return topic
    return None


def create_topic(data: Dict[str, Any]) -> int:
    """Create a new topic."""
    conn = get_db()
    cursor = conn.cursor()

    search_terms = json.dumps(data.get('search_terms', []))
    urls = json.dumps(data.get('urls', []))

    cursor.execute("""
        INSERT INTO topics (
            name, description, search_terms, urls,
            schedule_frequency, schedule_time, schedule_day,
            schedule_interval, email, enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('name'),
        data.get('description', ''),
        search_terms,
        urls,
        data.get('schedule_frequency', ''),
        data.get('schedule_time', ''),
        data.get('schedule_day', ''),
        data.get('schedule_interval', None),
        data.get('email', ''),
        1
    ))

    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id


def update_topic(topic_id: int, data: Dict[str, Any]) -> bool:
    """Update an existing topic."""
    conn = get_db()
    cursor = conn.cursor()

    search_terms = json.dumps(data.get('search_terms', []))
    urls = json.dumps(data.get('urls', []))

    cursor.execute("""
        UPDATE topics SET
            name = ?,
            description = ?,
            search_terms = ?,
            urls = ?,
            schedule_frequency = ?,
            schedule_time = ?,
            schedule_day = ?,
            schedule_interval = ?,
            email = ?,
            enabled = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('name'),
        data.get('description', ''),
        search_terms,
        urls,
        data.get('schedule_frequency', ''),
        data.get('schedule_time', ''),
        data.get('schedule_day', ''),
        data.get('schedule_interval', None),
        data.get('email', ''),
        data.get('enabled', 1),
        topic_id
    ))

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_topic(topic_id: int) -> bool:
    """Soft delete a topic."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE topics SET enabled = 0 WHERE id = ?", (topic_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# ============================================
# REPORT OPERATIONS
# ============================================

def create_report(topic_id: int, content: str, filepath: str) -> int:
    """Create a new report entry."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (topic_id, content, filepath, status, started_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        topic_id,
        content,
        filepath,
        'running',
        datetime.now().isoformat()
    ))

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def complete_report(report_id: int, status: str = 'completed'):
    """Mark a report as completed."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reports SET status = ?, completed_at = ?
        WHERE id = ?
    """, (
        status,
        datetime.now().isoformat(),
        report_id
    ))
    conn.commit()
    conn.close()


def get_reports_for_topic(topic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get reports for a topic."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reports
        WHERE topic_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (topic_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_report(topic_id: int) -> Optional[Dict[str, Any]]:
    """Get the latest report for a topic."""
    reports = get_reports_for_topic(topic_id, 1)
    return reports[0] if reports else None


# ============================================
# TRACE OPERATIONS
# ============================================

def add_trace(run_id: str, topic_id: int, step_number: int,
              agent: str, action: str, content: str = ''):
    """Add a trace entry."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO traces (run_id, topic_id, step_number, agent, action, content)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        topic_id,
        step_number,
        agent,
        action,
        content[:500] if content else ''
    ))
    conn.commit()
    conn.close()


def get_traces(run_id: str) -> List[Dict[str, Any]]:
    """Get all traces for a run."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM traces
        WHERE run_id = ?
        ORDER BY timestamp ASC
    """, (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================
# SETTINGS OPERATIONS
# ============================================

def get_setting(key: str, default: str = '') -> str:
    """Get a setting value."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key: str, value: str):
    """Set a setting value."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
    """, (key, value, value))
    conn.commit()
    conn.close()

# ============================================
# LLM PROVIDER SETTINGS
# ============================================

def get_llm_provider() -> str:
    """Get the current LLM provider from settings."""
    return get_setting('llm_provider', 'groq')


def set_llm_provider(provider: str) -> None:
    """Set the LLM provider in settings."""
    valid_providers = ['groq', 'openrouter']
    if provider not in valid_providers:
        raise ValueError(f"Invalid provider: {provider}. Must be one of {valid_providers}")
    set_setting('llm_provider', provider)