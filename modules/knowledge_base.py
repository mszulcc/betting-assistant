"""
Knowledge Base module — SQLite-backed domain knowledge store.
This is the project's OWN knowledge base (not the LLM).
Stores betting strategies, terminology, team analysis notes,
league insights, and FAQ.
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the SQLite knowledge base."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all knowledge base tables if they don't exist."""
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS betting_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            risk_level TEXT NOT NULL CHECK(risk_level IN ('low', 'medium', 'high')),
            category TEXT NOT NULL,
            example TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS betting_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            example_usage TEXT,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS team_analysis_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            league TEXT,
            season TEXT,
            strengths TEXT,
            weaknesses TEXT,
            form_notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS historical_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_description TEXT NOT NULL,
            prediction TEXT NOT NULL,
            reasoning TEXT,
            result TEXT,
            odds_taken REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS league_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_name TEXT NOT NULL UNIQUE,
            key_stats TEXT,
            trends TEXT,
            betting_tips TEXT,
            season TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS api_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            data TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Search functions — used by the query router to provide context to the LLM
# ---------------------------------------------------------------------------

def search_strategies(query: str, limit: int = 5) -> list[dict]:
    """Search betting strategies by name, category, or description."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT name, description, risk_level, category, example
           FROM betting_strategies
           WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
           ORDER BY name LIMIT ?""",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_terms(query: str, limit: int = 5) -> list[dict]:
    """Search betting terms by term or definition."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT term, definition, example_usage, category
           FROM betting_terms
           WHERE term LIKE ? OR definition LIKE ?
           ORDER BY term LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_team_notes(team_name: str) -> list[dict]:
    """Search team analysis notes by team name."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT team_name, league, season, strengths, weaknesses, form_notes
           FROM team_analysis_notes
           WHERE team_name LIKE ?
           ORDER BY updated_at DESC LIMIT 3""",
        (f"%{team_name}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_league_insights(league_name: str) -> list[dict]:
    """Search league insights by league name."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT league_name, key_stats, trends, betting_tips, season
           FROM league_insights
           WHERE league_name LIKE ?
           ORDER BY updated_at DESC LIMIT 3""",
        (f"%{league_name}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_faq(query: str, limit: int = 5) -> list[dict]:
    """Search FAQ by question or answer text."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT question, answer, category
           FROM faq
           WHERE question LIKE ? OR answer LIKE ?
           ORDER BY question LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_historical_tips(query: str, limit: int = 5) -> list[dict]:
    """Search historical betting tips."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT match_description, prediction, reasoning, result, odds_taken
           FROM historical_tips
           WHERE match_description LIKE ? OR prediction LIKE ? OR reasoning LIKE ?
           ORDER BY created_at DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_all(query: str) -> dict:
    """
    Broad search across all knowledge base tables.
    Returns a dict with results from each table.
    """
    return {
        "strategies": search_strategies(query),
        "terms": search_terms(query),
        "team_notes": search_team_notes(query),
        "league_insights": search_league_insights(query),
        "faq": search_faq(query),
        "historical_tips": search_historical_tips(query),
    }


def get_all_strategies() -> list[dict]:
    """Get all betting strategies."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT name, description, risk_level, category, example FROM betting_strategies ORDER BY category, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_terms() -> list[dict]:
    """Get all betting terms."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT term, definition, example_usage, category FROM betting_terms ORDER BY term"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_faq() -> list[dict]:
    """Get all FAQ entries."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT question, answer, category FROM faq ORDER BY category, question"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Cache functions for API responses
# ---------------------------------------------------------------------------

def get_cached(cache_key: str) -> Optional[str]:
    """Get cached API response if not expired."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM api_cache WHERE cache_key = ? AND expires_at > ?",
        (cache_key, datetime.utcnow().isoformat())
    ).fetchone()
    conn.close()
    return row["data"] if row else None


def set_cached(cache_key: str, data: str, ttl_seconds: int = 900):
    """Cache an API response with a TTL."""
    from datetime import timedelta
    expires = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO api_cache (cache_key, data, expires_at)
           VALUES (?, ?, ?)""",
        (cache_key, data, expires)
    )
    conn.commit()
    conn.close()


def clear_expired_cache():
    """Remove expired cache entries."""
    conn = _get_conn()
    conn.execute(
        "DELETE FROM api_cache WHERE expires_at <= ?",
        (datetime.utcnow().isoformat(),)
    )
    conn.commit()
    conn.close()


def get_kb_stats() -> dict:
    """Get counts for all KB tables — used in the UI dashboard."""
    conn = _get_conn()
    stats = {}
    for table in ["betting_strategies", "betting_terms", "team_analysis_notes",
                   "historical_tips", "league_insights", "faq"]:
        count = conn.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()["c"]
        stats[table] = count
    conn.close()
    return stats
