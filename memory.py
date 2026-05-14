import sqlite3
import time
from pathlib import Path

DB_PATH     = Path(__file__).parent / "memory.db"
REGULAR_AT  = 10   # interactions before a viewer is considered a regular
HISTORY_LEN = 5    # recent Q&As passed to the LLM as context
MAX_STORED  = 50   # max interactions kept per viewer (oldest pruned)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS viewers (
                username         TEXT    PRIMARY KEY,
                first_seen       REAL    NOT NULL,
                last_seen        REAL    NOT NULL,
                interaction_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    NOT NULL,
                question  TEXT    NOT NULL,
                answer    TEXT    NOT NULL,
                timestamp REAL    NOT NULL
            )
        """)


def save_interaction(username: str, question: str, answer: str):
    """Record a Q&A and update the viewer's profile."""
    now = time.time()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO viewers (username, first_seen, last_seen, interaction_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(username) DO UPDATE SET
                last_seen         = excluded.last_seen,
                interaction_count = interaction_count + 1
        """, (username, now, now))

        conn.execute("""
            INSERT INTO interactions (username, question, answer, timestamp)
            VALUES (?, ?, ?, ?)
        """, (username, question, answer, now))

        # Prune oldest entries beyond MAX_STORED
        conn.execute("""
            DELETE FROM interactions
            WHERE username = ?
              AND id NOT IN (
                  SELECT id FROM interactions
                  WHERE username = ?
                  ORDER BY timestamp DESC
                  LIMIT ?
              )
        """, (username, username, MAX_STORED))


def get_viewer_context(username: str) -> str:
    """
    Return a plain-text context block for the LLM about this viewer.
    Empty string if the viewer has never interacted before.
    """
    with _connect() as conn:
        viewer = conn.execute(
            "SELECT * FROM viewers WHERE username = ?", (username,)
        ).fetchone()

        if not viewer:
            return ""

        history = conn.execute("""
            SELECT question, answer FROM interactions
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (username, HISTORY_LEN)).fetchall()

    count = viewer["interaction_count"]
    lines = []

    if count >= REGULAR_AT:
        lines.append(f"{username} is a regular viewer with {count} past interactions.")
    else:
        lines.append(f"{username} has interacted {count} time(s) before.")

    if history:
        lines.append("Their recent questions and your past answers (oldest first):")
        for row in reversed(history):
            lines.append(f"  Q: {row['question']}")
            lines.append(f"  A: {row['answer']}")

    return "\n".join(lines)
