"""
Query Router module.
Categorizes user queries and retrieves relevant context from the
Knowledge Base and/or Live API to inject into the LLM prompt.
"""
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import AVAILABLE_LEAGUES
import modules.knowledge_base as kb
import modules.football_api as api

# Common betting terms to help routing
BETTING_TERMS_KEYWORDS = ["handicap", "asian", "over", "under", "btts", "value", "arbitrage", "stake", "bankroll", "accumulator", "parlay", "odds", "ev", "roi", "strategy", "strategies", "tip", "tips", "meaning", "what is"]

def analyze_query(query: str) -> dict:
    """Analyze the user's query to determine what data sources are needed."""
    query_lower = query.lower()
    intent = {
        "needs_kb_terms": False,
        "needs_kb_team_notes": False,
        "needs_kb_league_insights": False,
        "needs_kb_strategies": False,
        "needs_api_upcoming_matches": False,
        "needs_api_standings": False,
        "needs_api_team_search": False,
        "team_mentions": [],
        "league_mentions": [],
    }

    # 1. Check for terms & strategies
    if any(keyword in query_lower for keyword in BETTING_TERMS_KEYWORDS):
        intent["needs_kb_terms"] = True
        intent["needs_kb_strategies"] = True

    # 2. Check for league mentions
    for league_key, league_info in AVAILABLE_LEAGUES.items():
        if league_info["name"].lower() in query_lower or league_key.lower() in query_lower:
            intent["league_mentions"].append(league_info["code"])
            intent["needs_kb_league_insights"] = True

    # 3. Check for typical API intents
    if any(word in query_lower for word in ["match", "matches", "game", "games", "play", "playing", "weekend", "today", "tomorrow", "upcoming", "fixture"]):
        intent["needs_api_upcoming_matches"] = True

    if any(word in query_lower for word in ["table", "standings", "rank", "position", "leader", "points"]):
        intent["needs_api_standings"] = True
        if intent["league_mentions"]:
            intent["needs_api_standings"] = True

    # 4. Naive team extraction (looking for capitalized words not at start of sentence, or just searching all team notes)
    # To keep it simple without full NLP, we will just search the KB team notes with the whole query
    # and if we get hits, assume those teams were mentioned.
    intent["needs_kb_team_notes"] = True
    intent["needs_api_team_search"] = True

    return intent

def get_context_for_query(query: str) -> tuple[str, str]:
    """
    Route the query to appropriate data sources and build context strings.
    Returns (kb_context, api_context)
    """
    intent = analyze_query(query)
    kb_parts = []
    api_parts = []

    # --- Knowledge Base Context ---
    
    # Terms & Strategies
    if intent["needs_kb_terms"]:
        terms = kb.search_terms(query)
        if terms:
            kb_parts.append("Betting Terms Definitions:\n" + "\n".join([f"- **{t['term']}**: {t['definition']} (Example: {t['example_usage']})" for t in terms]))
            
    if intent["needs_kb_strategies"]:
        strategies = kb.search_strategies(query)
        if strategies:
            kb_parts.append("Relevant Betting Strategies:\n" + "\n".join([f"- **{s['name']}** ({s['risk_level']} risk): {s['description']}" for s in strategies]))

    # FAQ
    faqs = kb.search_faq(query, limit=2)
    if faqs:
        kb_parts.append("Relevant FAQ:\n" + "\n".join([f"- **Q: {f['question']}**\n  A: {f['answer']}" for f in faqs]))

    # League Insights
    if intent["league_mentions"]:
        for code in intent["league_mentions"]:
            league_name = next(l["name"] for l in AVAILABLE_LEAGUES.values() if l["code"] == code)
            insights = kb.search_league_insights(league_name)
            if insights:
                i = insights[0]
                kb_parts.append(f"League Insights for {league_name}:\n- Stats: {i['key_stats']}\n- Trends: {i['trends']}\n- Tips: {i['betting_tips']}")

    # Team Notes
    if intent["needs_kb_team_notes"]:
        # Extract potential words > 3 chars
        words = [w for w in query.split() if len(w) > 3]
        found_teams = set()
        for word in words:
            word_clean = re.sub(r'[^a-zA-Z0-9]', '', word)
            if len(word_clean) > 3:
                notes = kb.search_team_notes(word_clean)
                for note in notes:
                    if note['team_name'] not in found_teams:
                        kb_parts.append(f"Team Analysis for {note['team_name']} ({note['league']}):\n- Strengths: {note['strengths']}\n- Weaknesses: {note['weaknesses']}\n- Form: {note['form_notes']}")
                        found_teams.add(note['team_name'])

    # --- API Context ---
    
    # Standings
    if intent["needs_api_standings"]:
        if intent["league_mentions"]:
            for code in intent["league_mentions"][:1]: # Max 1 league to save tokens
                standings = api.get_standings(code)
                if standings:
                    top5 = standings[:5]
                    table_str = "\n".join([f"{s['position']}. {s['team']} - {s['points']} pts (W:{s['won']} D:{s['draw']} L:{s['lost']})" for s in top5])
                    api_parts.append(f"Top 5 Standings for League Code {code}:\n{table_str}\n...")
        else:
            api_parts.append("(User asked for standings but didn't specify a league. Ask which league they want.)")

    # Upcoming Matches
    if intent["needs_api_upcoming_matches"]:
        league_code = intent["league_mentions"][0] if intent["league_mentions"] else None
        matches = api.get_upcoming_matches(league_code, days_ahead=3)
        if matches:
            match_str = "\n".join([f"- {m['date']}: {m['home_team']} vs {m['away_team']} ({m['competition']})" for m in matches[:10]]) # limit to 10
            api_parts.append(f"Upcoming Matches:\n{match_str}")
        else:
            api_parts.append("No upcoming matches found for the specified criteria.")

    # Team Match History (if a team was found in query)
# Team Match History (tylko dla drużyn zidentyfikowanych w bazie wiedzy!)
    if intent["needs_api_team_search"] and found_teams:
         for team_name in found_teams:
            # Szukamy w API tylko konkretnej nazwy, którą potwierdziliśmy w KB
            teams = api.search_team_in_standings(team_name)
            if teams:
                t = teams[0]
                api_parts.append(f"Current Form for {t['team']} ({t['league']}): Pos {t['position']}, {t['points']} pts. GD: {t['goal_diff']}.")
                break # Zatrzymujemy po znalezieniu pierwszej drużyny, aby oszczędzać API

    # Format output
    kb_context = "\n\n".join(kb_parts) if kb_parts else ""
    api_context = "\n\n".join(api_parts) if api_parts else ""
    
    # Truncate if too long (simple protection)
    if len(kb_context) > 3000:
        kb_context = kb_context[:3000] + "...\n(Truncated)"
    if len(api_context) > 3000:
        api_context = api_context[:3000] + "...\n(Truncated)"

    return kb_context, api_context
