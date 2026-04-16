"""Session persistence — SQLite-backed storage for interview sessions.

Implements Suggestion 6: session persistence, history, replay, and
spaced-repetition tracking for weak competencies.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from models.schemas import (
    CompetencyTag,
    QuestionEvaluation,
    SessionReport,
    SessionState,
    TranscriptTurn,
)

DEFAULT_DB_PATH = Path('storage/db/sessions.sqlite3')


def _ensure_db(db_path: Path) -> sqlite3.Connection:
    """Create / open the SQLite database and ensure schema exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            started_at  TEXT NOT NULL,
            ended_at    TEXT,
            state_json  TEXT NOT NULL,
            report_json TEXT
        );

        CREATE TABLE IF NOT EXISTS transcript_turns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL REFERENCES sessions(id),
            turn_index  INTEGER NOT NULL,
            turn_json   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL REFERENCES sessions(id),
            question_id TEXT NOT NULL,
            eval_json   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS competency_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT NOT NULL REFERENCES sessions(id),
            competency    TEXT NOT NULL,
            score         REAL NOT NULL,
            recorded_at   TEXT NOT NULL
        );
    ''')
    conn.commit()
    return conn


class SessionStore:
    """Persistent session storage with history and spaced-repetition support."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _ensure_db(self.db_path)
        return self._conn

    # ── save ──────────────────────────────────────────────────────────

    def save_session(
        self,
        session_id: str,
        state: SessionState,
        transcript: list[TranscriptTurn],
        evaluations: list[QuestionEvaluation],
        report: Optional[SessionReport] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        state_json = state.model_dump_json()
        report_json = report.model_dump_json() if report else None

        self.conn.execute(
            'INSERT OR REPLACE INTO sessions (id, started_at, ended_at, state_json, report_json) '
            'VALUES (?, ?, ?, ?, ?)',
            (session_id, now, now, state_json, report_json),
        )
        # Transcript
        self.conn.execute('DELETE FROM transcript_turns WHERE session_id = ?', (session_id,))
        for idx, turn in enumerate(transcript):
            self.conn.execute(
                'INSERT INTO transcript_turns (session_id, turn_index, turn_json) VALUES (?, ?, ?)',
                (session_id, idx, turn.model_dump_json()),
            )
        # Evaluations
        self.conn.execute('DELETE FROM evaluations WHERE session_id = ?', (session_id,))
        for ev in evaluations:
            self.conn.execute(
                'INSERT INTO evaluations (session_id, question_id, eval_json) VALUES (?, ?, ?)',
                (session_id, ev.question_id, ev.model_dump_json()),
            )
        # Competency history for spaced repetition
        for ev in evaluations:
            score = ev.rubric_score.weighted_total
            # record the overall score per evaluation
            self.conn.execute(
                'INSERT INTO competency_history (session_id, competency, score, recorded_at) '
                'VALUES (?, ?, ?, ?)',
                (session_id, 'overall', score, now),
            )

        self.conn.commit()

    def save_competency_scores(
        self, session_id: str, competency_scores: dict[str, float],
    ) -> None:
        """Record per-competency scores for spaced repetition tracking."""
        now = datetime.now(timezone.utc).isoformat()
        for comp, score in competency_scores.items():
            self.conn.execute(
                'INSERT INTO competency_history (session_id, competency, score, recorded_at) '
                'VALUES (?, ?, ?, ?)',
                (session_id, comp, score, now),
            )
        self.conn.commit()

    # ── load ──────────────────────────────────────────────────────────

    def list_sessions(self, limit: int = 50) -> list[dict]:
        """Return recent sessions as dicts with id, started_at, ended_at."""
        rows = self.conn.execute(
            'SELECT id, started_at, ended_at FROM sessions ORDER BY started_at DESC LIMIT ?',
            (limit,),
        ).fetchall()
        return [{'id': r[0], 'started_at': r[1], 'ended_at': r[2]} for r in rows]

    def load_session_state(self, session_id: str) -> Optional[SessionState]:
        row = self.conn.execute(
            'SELECT state_json FROM sessions WHERE id = ?', (session_id,),
        ).fetchone()
        if row:
            return SessionState.model_validate_json(row[0])
        return None

    def load_transcript(self, session_id: str) -> list[TranscriptTurn]:
        rows = self.conn.execute(
            'SELECT turn_json FROM transcript_turns WHERE session_id = ? ORDER BY turn_index',
            (session_id,),
        ).fetchall()
        return [TranscriptTurn.model_validate_json(r[0]) for r in rows]

    def load_evaluations(self, session_id: str) -> list[QuestionEvaluation]:
        rows = self.conn.execute(
            'SELECT eval_json FROM evaluations WHERE session_id = ? ORDER BY id',
            (session_id,),
        ).fetchall()
        return [QuestionEvaluation.model_validate_json(r[0]) for r in rows]

    def load_report(self, session_id: str) -> Optional[SessionReport]:
        row = self.conn.execute(
            'SELECT report_json FROM sessions WHERE id = ?', (session_id,),
        ).fetchone()
        if row and row[0]:
            return SessionReport.model_validate_json(row[0])
        return None

    # ── spaced repetition ─────────────────────────────────────────────

    def get_weak_competencies(self, threshold: float = 5.0, recent_n: int = 5) -> list[str]:
        """Return competencies with average score below threshold in recent sessions."""
        rows = self.conn.execute('''
            SELECT competency, AVG(score) as avg_score
            FROM competency_history
            WHERE competency != 'overall'
            GROUP BY competency
            HAVING avg_score < ?
            ORDER BY avg_score ASC
        ''', (threshold,)).fetchall()
        return [r[0] for r in rows]

    def get_competency_trend(self, competency: str, limit: int = 10) -> list[dict]:
        """Return score trend for a competency across recent sessions."""
        rows = self.conn.execute('''
            SELECT session_id, score, recorded_at
            FROM competency_history
            WHERE competency = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        ''', (competency, limit)).fetchall()
        return [{'session_id': r[0], 'score': r[1], 'recorded_at': r[2]} for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
