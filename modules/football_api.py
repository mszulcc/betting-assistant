"""
Football API client for football-data.org (v4).
Fetches live match data, standings, and team information.
Includes caching via SQLite to respect rate limits (10 req/min free tier).
"""
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Optional

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import FOOTBALL_API_BASE_URL, FOOTBALL_DATA_API_KEY, API_CACHE_TTL_SECONDS, AVAILABLE_LEAGUES
from modules.knowledge_base import get_cached, set_cached


# Rate limiting
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 6.5  # seconds (10 req/min = 6s interval + buffer)


def _rate_limit():
    """Ensure we don't exceed 10 requests per minute."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _api_request(endpoint: str, params: dict = None) -> Optional[dict]:
    """
    Make a cached, rate-limited request to football-data.org.
    Returns parsed JSON or None on error.
    """
    if not FOOTBALL_DATA_API_KEY:
        return None

    # Build cache key
    cache_key = f"football_api:{endpoint}:{json.dumps(params or {}, sort_keys=True)}"

    # Check cache first
    cached = get_cached(cache_key)
    if cached:
        return json.loads(cached)

    # Rate limit then request
    _rate_limit()

    url = f"{FOOTBALL_API_BASE_URL}{endpoint}"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            set_cached(cache_key, json.dumps(data), API_CACHE_TTL_SECONDS)
            return data
        elif resp.status_code == 429:
            # Rate limited — wait and return None
            return None
        else:
            return None
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def get_upcoming_matches(league_code: int = None, days_ahead: int = 7) -> list[dict]:
    """
    Get upcoming matches, optionally filtered by league.
    Returns a simplified list of match dicts.
    """
    date_from = datetime.utcnow().strftime("%Y-%m-%d")
    date_to = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    if league_code:
        data = _api_request(
            f"/competitions/{league_code}/matches",
            {"dateFrom": date_from, "dateTo": date_to, "status": "SCHEDULED,TIMED"}
        )
    else:
        data = _api_request(
            "/matches",
            {"dateFrom": date_from, "dateTo": date_to}
        )

    if not data or "matches" not in data:
        return []

    return [_simplify_match(m) for m in data["matches"]]


def get_recent_matches(league_code: int = None, days_back: int = 7) -> list[dict]:
    """Get recently finished matches."""
    date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = datetime.utcnow().strftime("%Y-%m-%d")

    if league_code:
        data = _api_request(
            f"/competitions/{league_code}/matches",
            {"dateFrom": date_from, "dateTo": date_to, "status": "FINISHED"}
        )
    else:
        data = _api_request(
            "/matches",
            {"dateFrom": date_from, "dateTo": date_to, "status": "FINISHED"}
        )

    if not data or "matches" not in data:
        return []

    return [_simplify_match(m) for m in data["matches"]]


def get_standings(league_code: int) -> list[dict]:
    """Get current league standings/table."""
    data = _api_request(f"/competitions/{league_code}/standings")

    if not data or "standings" not in data:
        return []

    standings = []
    for standing_type in data["standings"]:
        if standing_type.get("type") == "TOTAL":
            for entry in standing_type.get("table", []):
                standings.append({
                    "position": entry.get("position"),
                    "team": entry.get("team", {}).get("name", "Unknown"),
                    "played": entry.get("playedGames", 0),
                    "won": entry.get("won", 0),
                    "draw": entry.get("draw", 0),
                    "lost": entry.get("lost", 0),
                    "goals_for": entry.get("goalsFor", 0),
                    "goals_against": entry.get("goalsAgainst", 0),
                    "goal_diff": entry.get("goalDifference", 0),
                    "points": entry.get("points", 0),
                })
    return standings


def get_team_matches(team_id: int, limit: int = 10, status: str = "FINISHED") -> list[dict]:
    """Get a team's recent or upcoming matches."""
    data = _api_request(
        f"/teams/{team_id}/matches",
        {"status": status, "limit": limit}
    )

    if not data or "matches" not in data:
        return []

    return [_simplify_match(m) for m in data["matches"]]


def get_head_to_head(match_id: int) -> dict:
    """Get head-to-head data for a specific match."""
    data = _api_request(f"/matches/{match_id}/head2head", {"limit": 10})

    if not data:
        return {}

    aggregates = data.get("aggregates", {})
    matches = [_simplify_match(m) for m in data.get("matches", [])]

    return {
        "total_matches": aggregates.get("numberOfMatches", 0),
        "home_wins": aggregates.get("homeTeam", {}).get("wins", 0),
        "away_wins": aggregates.get("awayTeam", {}).get("wins", 0),
        "draws": aggregates.get("homeTeam", {}).get("draws", 0),
        "recent_matches": matches[:5],
    }


def search_team_in_standings(team_name: str) -> list[dict]:
    """Search for a team across all available league standings."""
    results = []
    for league_key, league_info in AVAILABLE_LEAGUES.items():
        standings = get_standings(league_info["code"])
        for entry in standings:
            if team_name.lower() in entry["team"].lower():
                entry["league"] = league_info["name"]
                results.append(entry)
    return results


def get_competition_info(league_code: int) -> Optional[dict]:
    """Get basic competition information."""
    data = _api_request(f"/competitions/{league_code}")
    if not data:
        return None
    return {
        "name": data.get("name"),
        "area": data.get("area", {}).get("name"),
        "current_season": data.get("currentSeason", {}),
        "current_matchday": data.get("currentSeason", {}).get("currentMatchday"),
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _simplify_match(match: dict) -> dict:
    """Simplify a raw API match object into a clean dict."""
    utc_date = match.get("utcDate", "")
    try:
        dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        date_str = utc_date

    score = match.get("score", {})
    ft = score.get("fullTime", {})

    return {
        "id": match.get("id"),
        "competition": match.get("competition", {}).get("name", ""),
        "home_team": match.get("homeTeam", {}).get("name", "Unknown"),
        "away_team": match.get("awayTeam", {}).get("name", "Unknown"),
        "home_team_id": match.get("homeTeam", {}).get("id"),
        "away_team_id": match.get("awayTeam", {}).get("id"),
        "date": date_str,
        "status": match.get("status", ""),
        "matchday": match.get("matchday"),
        "home_score": ft.get("home"),
        "away_score": ft.get("away"),
    }


def is_api_configured() -> bool:
    """Check if the Football API key is configured."""
    return bool(FOOTBALL_DATA_API_KEY and FOOTBALL_DATA_API_KEY != "your_football_data_api_key_here")
