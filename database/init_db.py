"""
Database Schema & Initialization Script
Dream AI System - EEC10212
Reem Khalfan Aljabri (230390) - Database & Testing

Run this script once to create the SQLite database and tables.
After that, Flask-SQLAlchemy will manage everything automatically.

Usage: python init_db.py
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'dreams.db')
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def init_db():
    """Create the database and all tables from scratch."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign key enforcement (SQLite has this off by default)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ── users table ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            username     TEXT     NOT NULL UNIQUE,
            email        TEXT,
            password_hash TEXT   NOT NULL,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ── dreams table ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dreams (
            id         INTEGER  PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title      TEXT     DEFAULT 'Untitled Dream',
            content    TEXT     NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Index for fast user-based dream queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dreams_user
        ON dreams(user_id, created_at DESC);
    """)

    # ── analysis_results table ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id          INTEGER  PRIMARY KEY AUTOINCREMENT,
            dream_id    INTEGER  NOT NULL UNIQUE REFERENCES dreams(id) ON DELETE CASCADE,
            emotion     TEXT     NOT NULL,
            confidence  REAL     DEFAULT 0.0,
            keywords    TEXT     DEFAULT '[]',
            analysed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    # Backfill timestamps for older rows created without them.
    cursor.execute("""
        UPDATE dreams
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
    """)
    cursor.execute("""
        UPDATE analysis_results
        SET analysed_at = CURRENT_TIMESTAMP
        WHERE analysed_at IS NULL;
    """)
    cursor.execute("""
        UPDATE users
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
    """)
    conn.commit()

    print(f"Database initialised at: {DB_PATH}")
    print("Tables created: users, dreams, analysis_results")

    # Verify by listing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables confirmed: {[t[0] for t in tables]}")

    conn.close()


def seed_demo_data():
    """
    Insert a demo user and a few sample dreams so the app looks alive
    when demoed without needing to type everything manually.
    Only call this during development - never in production.
    """
    from password_utils import hash_password

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if demo user already exists
    cursor.execute("SELECT id FROM users WHERE username = 'demo';")
    if cursor.fetchone():
        print("Demo data already exists, skipping seed.")
        conn.close()
        return

    # Create demo user (password: "demo123")
    hashed = hash_password("demo123")
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?);",
        ("demo", "demo@example.com", hashed)
    )
    user_id = cursor.lastrowid

    # Sample dreams
    sample_dreams = [
        ("Exam Nightmare",
         "I was running to an exam hall but kept getting lost in corridors that never ended. "
         "Everyone else seemed to know where to go. I finally found the room but realised I hadn't "
         "studied anything and the paper was completely blank for me.",
         "stress", 0.87),
        ("Flying over the city",
         "I was flying above the city, slowly at first then faster. I could see the lights below "
         "and felt completely free. There was no fear at all, just joy and the wind. It was one "
         "of those dreams you don't want to wake up from.",
         "happiness", 0.91),
        ("Strange forest",
         "I was walking through a dark forest alone and something was following me. I couldn't "
         "see what it was but I could hear it behind me in the trees. I kept running but the "
         "trees kept getting thicker and closer together.",
         "fear", 0.83),
        ("Lost at the airport",
         "I was trying to catch a flight but my passport was missing and the gate kept changing. "
         "Every time I ran to the right gate it changed to a different terminal. I missed the flight "
         "and couldn't contact anyone.",
         "stress", 0.79),
        ("Swimming in the ocean",
         "I was swimming in a clear blue ocean and the water was warm. I could breathe underwater "
         "and saw colourful fish all around me. My family was there too and we were all laughing.",
         "happiness", 0.88),
    ]

    for title, content, emotion, confidence in sample_dreams:
        cursor.execute(
            "INSERT INTO dreams (user_id, title, content, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP);",
            (user_id, title, content)
        )
        dream_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO analysis_results (dream_id, emotion, confidence, keywords, analysed_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);",
            (dream_id, emotion, confidence, '["running", "lost", "dark", "flying", "forest"]')
        )

    conn.commit()
    print(f"Demo data seeded: user 'demo' created with {len(sample_dreams)} sample dreams.")
    print("Login with: username=demo, password=demo123")
    conn.close()


if __name__ == '__main__':
    init_db()
    seed_demo_data()
