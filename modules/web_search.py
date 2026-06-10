"""
Web Search module using Tavily API.
Performs real-time internet searches for match previews, injuries,
lineups, betting odds, and other live football data.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TAVILY_API_KEY


def _get_client():
    """Return a configured Tavily client, or None if not configured."""
    if not TAVILY_API_KEY:
        return None
    try:
        from tavily import TavilyClient
        return TavilyClient(api_key=TAVILY_API_KEY)
    except Exception:
        return None


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Run a web search and return a list of result dicts with 'title', 'url', 'content'.
    Returns empty list on failure.
    """
    client = _get_client()
    if not client:
        return []
    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,  # Get a short summarized answer too
        )
        results = []
        # Add the top-level summarized answer if available
        if response.get("answer"):
            results.append({
                "title": "Summary",
                "url": "",
                "content": response["answer"],
            })
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:600],  # Trim to save tokens
            })
        return results
    except Exception as e:
        return []


def search_match_preview(home_team: str, away_team: str, competition: str = "") -> str:
    """Search for match preview, predicted lineups, injuries, and odds."""
    comp_str = f" {competition}" if competition else ""
    query = f"{home_team} vs {away_team}{comp_str} 2026 preview injuries lineup betting odds"
    results = search_web(query, max_results=5)
    return _format_results(results, f"Match Preview: {home_team} vs {away_team}")


def search_team_news(team_name: str) -> str:
    """Search for latest team news — injuries, suspensions, form."""
    query = f"{team_name} 2026 injuries suspensions squad news latest"
    results = search_web(query, max_results=3)
    return _format_results(results, f"Team News: {team_name}")


def search_betting_odds(home_team: str, away_team: str) -> str:
    """Search for current betting odds for a match."""
    query = f"{home_team} vs {away_team} betting odds 1X2 over under 2026"
    results = search_web(query, max_results=3)
    return _format_results(results, f"Betting Odds: {home_team} vs {away_team}")


def _format_results(results: list[dict], header: str) -> str:
    """Format search results into a readable string for the LLM context."""
    if not results:
        return ""
    parts = [f"=== {header} (Web Search) ==="]
    for r in results:
        if r["title"] == "Summary":
            parts.append(f"📝 {r['content']}")
        else:
            title = r["title"] or r["url"]
            parts.append(f"• {title}:\n  {r['content']}")
    return "\n\n".join(parts)


def is_web_search_configured() -> bool:
    """Check if Tavily API key is configured."""
    return bool(TAVILY_API_KEY)
