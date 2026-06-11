"""
ELO Ratings module — fetches and parses national team ELO data
from eloratings.net (World.tsv, latest.tsv, fixtures.tsv).

Team code resolution: en.teams.tsv (local file in project root)
Tournament resolution: en.tournaments.tsv (local file in project root)

=== World.tsv columns (tab-separated) ===
  0: rank_current
  1: rank_previous
  2: team_code (e.g. "ES", "MX", "ZA")
  3: elo_current
  4: rank_1yr_ago
  5: elo_1yr_ago
  6: rank_5yr_ago
  7: elo_5yr_ago
  8: rank_max
  9: elo_max
  ... (change/historical data)

=== latest.tsv columns ===
  0: year
  1: month
  2: day
  3: home_code
  4: away_code
  5: home_score
  6: away_score
  7: tournament_code
  8: venue_code        (country code of host nation, or blank)
  9: elo_diff          (signed: home_elo - away_elo before match)
  10: home_elo          (before match)
  11: away_elo          (before match)
  12: home_elo_change   (e.g. "+5" or "−3")
  13: away_elo_change
  14: home_rank
  15: away_rank

=== fixtures.tsv columns ===
  0: year
  1: month (00 = month unknown)
  2: day   (00 = day unknown)
  3: home_code
  4: away_code
  5: tournament_code
  6: venue_code
  7: home_rank
  8: away_rank
  9: home_elo
  10: away_elo
  11: home_win_prob (%)
  12: elo_diff (signed)
  13+: ELO change estimates (pairs: +if_win, +if_draw, +if_loss ...)
"""

import os
import sys
import time
import urllib.request
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE = "https://www.eloratings.net"
ELO_TSV_URL      = f"{_BASE}/World.tsv"
LATEST_TSV_URL   = f"{_BASE}/latest.tsv"
FIXTURES_TSV_URL = f"{_BASE}/fixtures.tsv"

_ROOT = os.path.dirname(os.path.dirname(__file__))
TEAMS_TSV_PATH       = os.path.join(_ROOT, "en.teams.tsv")
TOURNAMENTS_TSV_PATH = os.path.join(_ROOT, "en.tournaments.tsv")

# ---------------------------------------------------------------------------
# In-memory caches (ttl in seconds)
# ---------------------------------------------------------------------------

_cache_ratings: dict  = {"data": None, "fetched_at": 0.0, "ttl": 3600}
_cache_latest:  dict  = {"data": None, "fetched_at": 0.0, "ttl": 900}   # 15 min
_cache_fixtures: dict = {"data": None, "fetched_at": 0.0, "ttl": 1800}  # 30 min

# ---------------------------------------------------------------------------
# Reference data loaders (teams + tournaments)
# ---------------------------------------------------------------------------

def _load_team_names() -> dict[str, list[str]]:
    """
    Parse en.teams.tsv → { code: [canonical_name, alias1, alias2, ...] }
    """
    mapping: dict[str, list[str]] = {}
    if not os.path.exists(TEAMS_TSV_PATH):
        return mapping
    with open(TEAMS_TSV_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            code = parts[0].strip()
            if "_loc" in code:
                continue
            names = [p.strip() for p in parts[1:] if p.strip()]
            if names:
                mapping[code] = names
    return mapping


def _load_tournament_names() -> dict[str, str]:
    """
    Parse en.tournaments.tsv → { code: canonical_name }
    """
    mapping: dict[str, str] = {}
    if not os.path.exists(TOURNAMENTS_TSV_PATH):
        return mapping
    with open(TOURNAMENTS_TSV_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            code = parts[0].strip()
            name = parts[1].strip()
            if code and name:
                mapping[code] = name
    return mapping


# Singleton reference data (loaded once)
_team_names: dict[str, list[str]] | None = None
_tournament_names: dict[str, str] | None = None


def _teams() -> dict[str, list[str]]:
    global _team_names
    if _team_names is None:
        _team_names = _load_team_names()
    return _team_names


def _tournaments() -> dict[str, str]:
    global _tournament_names
    if _tournament_names is None:
        _tournament_names = _load_tournament_names()
    return _tournament_names


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _fetch_tsv(url: str) -> str:
    """Fetch a TSV URL and return its raw text, or '' on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BetAssistBot/1.0 (educational project)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[ELO] Failed to fetch {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _resolve_team(code: str) -> str:
    """Return canonical team name for a code, or the code itself."""
    names = _teams().get(code.strip(), [])
    return names[0] if names else code.strip()


def _resolve_tournament(code: str) -> str:
    """Return canonical tournament name for a code, or the code itself."""
    return _tournaments().get(code.strip(), code.strip())


def _safe_int(val: str) -> Optional[int]:
    """Parse an integer that may use the unicode minus sign '−'."""
    try:
        return int(val.replace("−", "-").strip())
    except (ValueError, AttributeError):
        return None


def _parse_ratings(raw: str) -> list[dict]:
    """Parse World.tsv into ELO ranking records."""
    records = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        try:
            rank_current  = int(parts[0])
            rank_previous = int(parts[1])
            code = parts[2].strip()
            elo  = int(parts[3])
        except (ValueError, IndexError):
            continue

        elo_1yr = _safe_int(parts[5]) if len(parts) > 5 else None
        elo_5yr = _safe_int(parts[7]) if len(parts) > 7 else None
        elo_max = _safe_int(parts[9]) if len(parts) > 9 else None

        names         = _teams().get(code, [])
        canonical     = names[0] if names else code

        records.append({
            "rank":            rank_current,
            "rank_previous":   rank_previous,
            "code":            code,
            "name":            canonical,
            "aliases":         names,
            "elo":             elo,
            "elo_1yr_ago":     elo_1yr,
            "elo_5yr_ago":     elo_5yr,
            "elo_all_time_max": elo_max,
        })
    return records


def _parse_date(year: str, month: str, day: str) -> str:
    """Build a human-readable date string, handling '00' placeholders."""
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        m_str = months[m] if 1 <= m <= 12 else "?"
        d_str = str(d) if d > 0 else "?"
        return f"{d_str} {m_str} {y}"
    except Exception:
        return f"{year}-{month}-{day}"


def _parse_latest(raw: str) -> list[dict]:
    """Parse latest.tsv into recent match result records."""
    results = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 14:
            continue
        try:
            year, month, day = parts[0], parts[1], parts[2]
            home_code  = parts[3].strip()
            away_code  = parts[4].strip()
            home_score = int(parts[5])
            away_score = int(parts[6])
            tourn_code = parts[7].strip()
            venue_code = parts[8].strip() if len(parts) > 8 else ""
            home_elo   = _safe_int(parts[10]) if len(parts) > 10 else None
            away_elo   = _safe_int(parts[11]) if len(parts) > 11 else None
            home_elo_change = parts[12].strip() if len(parts) > 12 else ""
            away_elo_change = parts[13].strip() if len(parts) > 13 else ""
            home_rank  = _safe_int(parts[14]) if len(parts) > 14 else None
            away_rank  = _safe_int(parts[15]) if len(parts) > 15 else None
        except (ValueError, IndexError):
            continue

        results.append({
            "date":             _parse_date(year, month, day),
            "home_team":        _resolve_team(home_code),
            "away_team":        _resolve_team(away_code),
            "home_code":        home_code,
            "away_code":        away_code,
            "home_score":       home_score,
            "away_score":       away_score,
            "tournament":       _resolve_tournament(tourn_code),
            "tournament_code":  tourn_code,
            "venue":            _resolve_team(venue_code) if venue_code else "Neutral",
            "home_elo":         home_elo,
            "away_elo":         away_elo,
            "home_elo_change":  home_elo_change,
            "away_elo_change":  away_elo_change,
            "home_rank":        home_rank,
            "away_rank":        away_rank,
        })
    return results


def _parse_fixtures(raw: str) -> list[dict]:
    """Parse fixtures.tsv into upcoming match records."""
    fixtures = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 11:
            continue
        try:
            year, month, day = parts[0], parts[1], parts[2]
            home_code  = parts[3].strip()
            away_code  = parts[4].strip()
            tourn_code = parts[5].strip()
            venue_code = parts[6].strip() if len(parts) > 6 else ""
            home_rank  = _safe_int(parts[7]) if len(parts) > 7 else None
            away_rank  = _safe_int(parts[8]) if len(parts) > 8 else None
            home_elo   = _safe_int(parts[9]) if len(parts) > 9 else None
            away_elo   = _safe_int(parts[10]) if len(parts) > 10 else None
            win_prob   = _safe_int(parts[11]) if len(parts) > 11 else None  # home win %
            elo_diff   = _safe_int(parts[12]) if len(parts) > 12 else None
        except (ValueError, IndexError):
            continue

        fixtures.append({
            "date":            _parse_date(year, month, day),
            "home_team":       _resolve_team(home_code),
            "away_team":       _resolve_team(away_code),
            "home_code":       home_code,
            "away_code":       away_code,
            "tournament":      _resolve_tournament(tourn_code),
            "tournament_code": tourn_code,
            "venue":           _resolve_team(venue_code) if venue_code else "Neutral",
            "home_rank":       home_rank,
            "away_rank":       away_rank,
            "home_elo":        home_elo,
            "away_elo":        away_elo,
            "home_win_prob":   win_prob,
            "draw_prob":       None,  # not directly available in TSV
            "away_win_prob":   (100 - win_prob) if win_prob is not None else None,
            "elo_diff":        elo_diff,
        })
    return fixtures


# ---------------------------------------------------------------------------
# Cache-aware data accessors
# ---------------------------------------------------------------------------

def _get_ratings() -> list[dict]:
    global _cache_ratings
    now = time.time()
    if _cache_ratings["data"] is None or (now - _cache_ratings["fetched_at"]) > _cache_ratings["ttl"]:
        _cache_ratings["data"] = _parse_ratings(_fetch_tsv(ELO_TSV_URL))
        _cache_ratings["fetched_at"] = now
    return _cache_ratings["data"]


def _get_latest() -> list[dict]:
    global _cache_latest
    now = time.time()
    if _cache_latest["data"] is None or (now - _cache_latest["fetched_at"]) > _cache_latest["ttl"]:
        _cache_latest["data"] = _parse_latest(_fetch_tsv(LATEST_TSV_URL))
        _cache_latest["fetched_at"] = now
    return _cache_latest["data"]


def _get_fixtures() -> list[dict]:
    global _cache_fixtures
    now = time.time()
    if _cache_fixtures["data"] is None or (now - _cache_fixtures["fetched_at"]) > _cache_fixtures["ttl"]:
        _cache_fixtures["data"] = _parse_fixtures(_fetch_tsv(FIXTURES_TSV_URL))
        _cache_fixtures["fetched_at"] = now
    return _cache_fixtures["data"]


# ---------------------------------------------------------------------------
# Public: team ranking lookup
# ---------------------------------------------------------------------------

def find_team(name: str) -> Optional[dict]:
    """
    Find a team by any name variant (case-insensitive, partial match fallback).
    Returns the ELO ranking record or None.
    """
    name_lower = name.strip().lower()
    data = _get_ratings()
    # 1. Exact match (canonical name)
    for r in data:
        if r["name"].lower() == name_lower:
            return r
    # 2. Exact alias match
    for r in data:
        for alias in r.get("aliases", []):
            if alias.lower() == name_lower:
                return r
    # 3. Partial match — name_lower contained in canonical
    for r in data:
        if name_lower in r["name"].lower():
            return r
    # 4. Partial match — name_lower contained in any alias
    for r in data:
        for alias in r.get("aliases", []):
            if name_lower in alias.lower():
                return r
    return None


def get_elo_for_teams(teams: list[str]) -> list[dict]:
    """Return ELO records for a list of team name strings (found ones only)."""
    seen_codes: set[str] = set()
    results = []
    for name in teams:
        record = find_team(name)
        if record and record["code"] not in seen_codes:
            seen_codes.add(record["code"])
            results.append(record)
    return results


def get_top_teams(n: int = 20) -> list[dict]:
    """Return the top-N ranked national teams."""
    return sorted(_get_ratings(), key=lambda r: r["rank"])[:n]


# ---------------------------------------------------------------------------
# Public: recent results
# ---------------------------------------------------------------------------

def get_recent_results(limit: int = 20) -> list[dict]:
    """Return the most recent international matches (from latest.tsv)."""
    return _get_latest()[:limit]


def find_results_for_team(team_name: str, limit: int = 10) -> list[dict]:
    """
    Return recent results involving a specific team.
    Matches by team name (canonical or alias).
    """
    record = find_team(team_name)
    if not record:
        return []
    code = record["code"]
    all_results = _get_latest()
    filtered = [
        r for r in all_results
        if r["home_code"] == code or r["away_code"] == code
    ]
    return filtered[:limit]


def find_results_for_match(home_name: str, away_name: str) -> Optional[dict]:
    """
    Find the most recent result between two specific teams (any order).
    Returns a single match dict or None.
    """
    home_rec = find_team(home_name)
    away_rec = find_team(away_name)
    if not home_rec or not away_rec:
        return None
    hc, ac = home_rec["code"], away_rec["code"]
    for r in _get_latest():
        if (r["home_code"] == hc and r["away_code"] == ac) or \
           (r["home_code"] == ac and r["away_code"] == hc):
            return r
    return None


# ---------------------------------------------------------------------------
# Public: upcoming fixtures
# ---------------------------------------------------------------------------

def get_upcoming_fixtures(limit: int = 20) -> list[dict]:
    """Return the next upcoming international fixtures (all tournaments)."""
    return _get_fixtures()[:limit]


def find_fixture_for_match(home_name: str, away_name: str) -> Optional[dict]:
    """
    Find an upcoming fixture between two specific teams (any order).
    Returns the fixture dict or None.
    """
    home_rec = find_team(home_name)
    away_rec = find_team(away_name)
    if not home_rec or not away_rec:
        return None
    hc, ac = home_rec["code"], away_rec["code"]
    for f in _get_fixtures():
        if (f["home_code"] == hc and f["away_code"] == ac) or \
           (f["home_code"] == ac and f["away_code"] == hc):
            return f
    return None


def find_fixtures_for_team(team_name: str, limit: int = 5) -> list[dict]:
    """Return upcoming fixtures for a given team."""
    record = find_team(team_name)
    if not record:
        return []
    code = record["code"]
    return [
        f for f in _get_fixtures()
        if f["home_code"] == code or f["away_code"] == code
    ][:limit]


# ---------------------------------------------------------------------------
# Public: LLM-ready formatting
# ---------------------------------------------------------------------------

def format_elo_for_llm(teams: list[str]) -> str:
    """
    Build a formatted string with ELO rankings + recent results + upcoming fixture
    for the given teams, ready to be injected into the LLM prompt context.
    """
    records = get_elo_for_teams(teams)
    if not records:
        return ""

    lines = ["=== ELO World Rankings (eloratings.net) ==="]

    # --- Rankings ---
    for r in records:
        trend = ""
        if r.get("elo_1yr_ago"):
            diff = r["elo"] - r["elo_1yr_ago"]
            trend = f" | Trend (1yr): {'+' if diff >= 0 else ''}{diff} ELO"
        lines.append(
            f"[ELO] **{r['name']}** — Rank #{r['rank']} | ELO: {r['elo']}{trend}"
        )

    # Comparative note for exactly 2 teams
    if len(records) == 2:
        diff = records[0]["elo"] - records[1]["elo"]
        stronger = records[0]["name"] if diff > 0 else records[1]["name"]
        lines.append(
            f"[ELO Comparison] Gap: {abs(diff)} pts — **{stronger}** is statistically stronger."
        )

    # --- Upcoming fixture (if 2 teams detected) ---
    if len(records) == 2:
        fix = find_fixture_for_match(records[0]["name"], records[1]["name"])
        if fix:
            lines.append("")
            lines.append("=== Upcoming Fixture (eloratings.net) ===")
            prob_str = ""
            if fix["home_win_prob"] is not None:
                prob_str = (
                    f" | Win probabilities: {fix['home_team']} {fix['home_win_prob']}%"
                    f" / {fix['away_team']} {fix['away_win_prob']}%"
                )
            lines.append(
                f"[Fixture] {fix['date']} | {fix['home_team']} vs {fix['away_team']}"
                f" | {fix['tournament']} | Venue: {fix['venue']}{prob_str}"
            )

    # --- Recent results (last 5 for each detected team, or h2h if 2 teams) ---
    if len(records) == 2:
        recent = find_results_for_match(records[0]["name"], records[1]["name"])
        if recent:
            lines.append("")
            lines.append("=== Most Recent H2H Result (eloratings.net) ===")
            winner = "Draw"
            if recent["home_score"] > recent["away_score"]:
                winner = f"{recent['home_team']} won"
            elif recent["away_score"] > recent["home_score"]:
                winner = f"{recent['away_team']} won"
            lines.append(
                f"[H2H] {recent['date']} | {recent['home_team']} {recent['home_score']}-{recent['away_score']}"
                f" {recent['away_team']} | {recent['tournament']} | {winner}"
            )

    # --- Recent form for each team (last 5 results) ---
    lines.append("")
    lines.append("=== Recent Form (eloratings.net) ===")
    for r in records:
        team_results = find_results_for_team(r["name"], limit=5)
        if not team_results:
            continue
        form_parts = []
        for m in team_results:
            if m["home_code"] == r["code"]:
                opp = m["away_team"]
                gs, ga = m["home_score"], m["away_score"]
                elo_ch = m["home_elo_change"]
            else:
                opp = m["home_team"]
                gs, ga = m["away_score"], m["home_score"]
                elo_ch = m["away_elo_change"]
            result = "W" if gs > ga else ("D" if gs == ga else "L")
            form_parts.append(f"{result} {gs}-{ga} vs {opp} ({m['date']}, ELO{elo_ch})")
        lines.append(f"[{r['name']}] " + " | ".join(form_parts))

    # Normalise unicode minus sign so the string is ASCII-safe
    return "\n".join(lines).replace("\u2212", "-")


def is_configured() -> bool:
    """Always True — no API key needed."""
    return True
