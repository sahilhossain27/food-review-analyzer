from contextlib import closing
from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().with_name("feedback.db")


def init_db() -> None:
    """Create the feedback table if it does not already exist."""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                label TEXT NOT NULL CHECK (label IN ('positive', 'negative', 'neutral')),
                score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
                theme TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_feedback(text: str, label: str, score: int, theme: str) -> None:
    """Save a review and its analysis."""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as connection:
        connection.execute(
            "INSERT INTO feedback (text, label, score, theme) VALUES (?, ?, ?, ?)",
            (text, label, score, theme),
        )
        connection.commit()


def list_feedback(limit: int = 50) -> list[dict[str, object]]:
    """Return the most recent feedback records first."""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, text, label, score, theme, created_at
            FROM feedback
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Feedback database ready: {DB_PATH}")
