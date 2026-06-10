"""
The Odds API client (v4) — https://the-odds-api.com
Fetches live betting odds from real bookmakers for upcoming football matches.
Free tier: 500 requests/month. Uses SQLite cache (15 min TTL) to preserve quota.

Supported markets:
  h2h    — 1X2 (win/draw/win)
  totals — Over/Under goals
"""
import json
import requests
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import ODDS_API_KEY, API_CACHE_TTL_SECONDS
from modules.knowledge_base import get_cached, set_cached

_BASE_URL = "https://api.the-odds-api.com/v4"

# Mapping from football-data.org league codes to Odds API sport keys
LEAGUE_TO_ODDS_SPORT = {
    2000: "soccer_fifa_world_cup",
    2001: "soccer_uefa_champs_league",
    2021: "soccer_england_league1",        # Premier League uses epl key
    2002: "soccer_germany_bundesliga",
    2019: "soccer_italy_serie_a",
    2014: "soccer_spain_la_liga",
    2015: "soccer_france_ligue_one",
}

# Better mapping for EPL
_EPL_SPORT_KEY = "soccer_epl"

# Preferred bookmakers for EU region (display order)
_PREFERRED_BOOKS = ["Pinnacle", "Betfair", "Unibet", "Marathon Bet", "bet365", "William Hill"]


def _request(endpoint: str, params: dict) -> dict | None:
    """Cached GET request to The Odds API."""
    if not ODDS_API_KEY:
        return None

    cache_key = f"odds_api:{endpoint}:{json.dumps(params, sort_keys=True)}"
    cached = get_cached(cache_key)
    if cached:
        return json.loads(cached)

    try:
        url = f"{_BASE_URL}{endpoint}"
        params["apiKey"] = ODDS_API_KEY
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            set_cached(cache_key, json.dumps(data), API_CACHE_TTL_SECONDS)
            return data
        return None
    except requests.RequestException:
        return None


def get_odds_for_sport(sport_key: str, markets: str = "h2h,totals", region: str = "eu") -> list[dict]:
    """
    Fetch all upcoming match odds for a given sport key.
    Returns a list of simplified match-odds dicts.
    """
    data = _request(f"/sports/{sport_key}/odds", {
        "regions": region,
        "markets": markets,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    })
    if not data or not isinstance(data, list):
        return []
    return [_simplify_game(g) for g in data]


def find_match_odds(home_team: str, away_team: str, sport_keys: list[str] = None) -> dict | None:
    """
    Search for odds for a specific match by team names (fuzzy match).
    Tries multiple sport keys if provided.
    Returns a simplified odds dict or None.
    """
    if sport_keys is None:
        sport_keys = ["soccer_fifa_world_cup", "soccer_epl", "soccer_germany_bundesliga",
                      "soccer_italy_serie_a", "soccer_spain_la_liga", "soccer_france_ligue_one",
                      "soccer_uefa_champs_league"]

    home_lower = home_team.lower()
    away_lower = away_team.lower()

    for sport_key in sport_keys:
        games = get_odds_for_sport(sport_key)
        for game in games:
            g_home = game["home_team"].lower()
            g_away = game["away_team"].lower()
            if (home_lower in g_home or g_home in home_lower) and \
               (away_lower in g_away or g_away in away_lower):
                return game
            # Also try reversed
            if (away_lower in g_home or g_home in away_lower) and \
               (home_lower in g_away or g_away in home_lower):
                return game
    return None


def get_wc_odds() -> list[dict]:
    """Get all current FIFA World Cup 2026 odds."""
    return get_odds_for_sport("soccer_fifa_world_cup")


def format_odds_for_llm(game: dict) -> str:
    """Format a game's odds into a readable string for LLM context."""
    if not game:
        return ""

    home = game["home_team"]
    away = game["away_team"]
    date = game.get("date", "")[:10]
    lines = [f"📊 **Betting Odds: {home} vs {away}** ({date})"]

    # H2H / 1X2
    if game.get("h2h"):
        h = game["h2h"]
        lines.append(
            f"  **1X2 (Win/Draw/Win):** "
            f"{home} = {h.get('home', 'N/A')} | "
            f"Draw = {h.get('draw', 'N/A')} | "
            f"{away} = {h.get('away', 'N/A')}"
            f"  *(source: {h.get('bookmaker', '?')})*"
        )
        # Implied probabilities
        try:
            ph = round(100 / h['home'], 1)
            pd = round(100 / h['draw'], 1)
            pa = round(100 / h['away'], 1)
            lines.append(f"  Implied probabilities: {home} {ph}% | Draw {pd}% | {away} {pa}%")
        except (KeyError, ZeroDivisionError, TypeError):
            pass

    # Totals (O/U)
    if game.get("totals"):
        t = game["totals"]
        lines.append(
            f"  **Over/Under {t.get('point', 2.5)} goals:** "
            f"Over = {t.get('over', 'N/A')} | Under = {t.get('under', 'N/A')}"
            f"  *(source: {t.get('bookmaker', '?')})*"
        )

    # All bookmakers summary
    if game.get("all_h2h"):
        lines.append("  **All bookmakers (1X2):**")
        for bm_name, odds in list(game["all_h2h"].items())[:5]:
            lines.append(f"    - {bm_name}: {home} {odds['home']} | Draw {odds['draw']} | {away} {odds['away']}")

    return "\n".join(lines)


def _simplify_game(game: dict) -> dict:
    """Simplify raw Odds API game data into a clean dict."""
    result = {
        "id": game.get("id"),
        "sport": game.get("sport_key"),
        "home_team": game.get("home_team", ""),
        "away_team": game.get("away_team", ""),
        "date": game.get("commence_time", "")[:10],
        "h2h": None,
        "totals": None,
        "all_h2h": {},
    }

    bookmakers = game.get("bookmakers", [])

    # Find best bookmaker (prefer Pinnacle, then others)
    def _book_priority(bm):
        title = bm.get("title", "")
        for i, pref in enumerate(_PREFERRED_BOOKS):
            if pref.lower() in title.lower():
                return i
        return 99

    sorted_books = sorted(bookmakers, key=_book_priority)

    for bm in sorted_books:
        bm_title = bm.get("title", "Unknown")
        for market in bm.get("markets", []):
            mkey = market.get("key")
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

            if mkey == "h2h":
                # Store all bookmakers
                result["all_h2h"][bm_title] = {
                    "home": outcomes.get(game.get("home_team", ""), "N/A"),
                    "draw": outcomes.get("Draw", "N/A"),
                    "away": outcomes.get(game.get("away_team", ""), "N/A"),
                }
                # Best (first preferred) bookmaker as primary
                if result["h2h"] is None:
                    result["h2h"] = {
                        "home": outcomes.get(game.get("home_team", ""), "N/A"),
                        "draw": outcomes.get("Draw", "N/A"),
                        "away": outcomes.get(game.get("away_team", ""), "N/A"),
                        "bookmaker": bm_title,
                    }

            elif mkey == "totals" and result["totals"] is None:
                over_out = next((o for o in market.get("outcomes", []) if o["name"] == "Over"), None)
                under_out = next((o for o in market.get("outcomes", []) if o["name"] == "Under"), None)
                if over_out:
                    result["totals"] = {
                        "point": over_out.get("point", 2.5),
                        "over": over_out.get("price", "N/A"),
                        "under": under_out.get("price", "N/A") if under_out else "N/A",
                        "bookmaker": bm_title,
                    }

    return result


def is_configured() -> bool:
    return bool(ODDS_API_KEY)
