"""
Query Router module.
Categorizes user queries and retrieves relevant context from the
Knowledge Base and/or Live API to inject into the LLM prompt.
"""
import re
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import AVAILABLE_LEAGUES
import modules.knowledge_base as kb
import modules.football_api as api
import modules.web_search as ws
import modules.odds_api as odds_api

# Common betting terms to help routing
BETTING_TERMS_KEYWORDS = ["handicap", "asian", "over", "under", "btts", "value", "arbitrage", "stake", "bankroll", "accumulator", "parlay", "odds", "ev", "roi", "strategy", "strategies", "tip", "tips", "meaning", "what is"]

# World Cup / international tournament keywords
WC_KEYWORDS = ["world cup", "mundial", "fifa", "wc", "world cup 2026", "tournament"]

# National teams commonly asked about - used for direct team name extraction from query
NATIONAL_TEAMS = [
    "mexico", "south africa", "usa", "united states", "canada", "brazil", "argentina",
    "germany", "france", "spain", "england", "portugal", "italy", "netherlands",
    "poland", "czechia", "south korea", "japan", "australia", "morocco", "senegal",
    "nigeria", "egypt", "qatar", "switzerland", "belgium", "croatia", "serbia",
    "denmark", "sweden", "norway", "ukraine", "turkey", "greece", "scotland",
    "wales", "ireland", "slovakia", "hungary", "romania", "albania",
    "colombia", "chile", "uruguay", "peru", "ecuador", "venezuela",
    "iran", "saudi arabia", "iraq", "australia", "new zealand", "ghana",
    "cameroon", "ivory coast", "mali", "algeria", "tunisia", "india",
    "china", "indonesia", "thailand", "vietnam", "bosnia", "bosnia-herzegovina",
    "paraguay", "bolivia", "honduras", "costa rica", "panama", "jamaica",
]

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
    if any(word in query_lower for word in ["match", "matches", "game", "games", "play", "playing", "weekend", "today", "tomorrow", "upcoming", "fixture", "analysis", "predict", "prediction", "bet", "betting"]):
        intent["needs_api_upcoming_matches"] = True

    if any(word in query_lower for word in ["table", "standings", "rank", "position", "leader", "points"]):
        intent["needs_api_standings"] = True
        if intent["league_mentions"]:
            intent["needs_api_standings"] = True

    # 4. Detect World Cup context
    if any(kw in query_lower for kw in WC_KEYWORDS):
        if 2000 not in intent["league_mentions"]:
            intent["league_mentions"].append(2000)  # WC code
        intent["needs_api_upcoming_matches"] = True

    # 5. Detect national team mentions directly from query text
    mentioned_national_teams = [t for t in NATIONAL_TEAMS if t in query_lower]
    intent["mentioned_national_teams"] = mentioned_national_teams
    if mentioned_national_teams:
        # If national teams are mentioned, assume World Cup context and fetch WC fixtures
        if 2000 not in intent["league_mentions"]:
            intent["league_mentions"].append(2000)
        intent["needs_api_upcoming_matches"] = True
        intent["needs_api_recent_matches"] = True
    else:
        intent["needs_api_recent_matches"] = False

    # 6. Determine if web search is needed
    # Trigger on: match analysis, injuries, odds, lineups, team news, or any team mention
    intent["needs_web_search"] = bool(
        mentioned_national_teams
        or any(w in query_lower for w in [
            "injur", "lineup", "squad", "suspend", "absent", "miss",
            "odds", "kurs", "typowanie", "prognoz", "analiz", "preview",
            "predict", "news", "form", "head to head", "h2h",
        ])
        or intent["needs_api_upcoming_matches"]
    )

    # 7. Naive team extraction for club teams via KB
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
    found_teams = set()
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
        # If national teams mentioned, always check WC fixtures first
        league_codes_to_check = intent["league_mentions"] if intent["league_mentions"] else [None]
        all_upcoming = []
        for lc in league_codes_to_check[:2]:  # max 2 leagues
            matches = api.get_upcoming_matches(lc, days_ahead=7)
            all_upcoming.extend(matches)
        # Deduplicate by match id
        seen_ids = set()
        unique_matches = []
        for m in all_upcoming:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique_matches.append(m)
        # If national teams mentioned, filter to show relevant matches first
        national_teams_lower = intent.get("mentioned_national_teams", [])
        if national_teams_lower:
            relevant = [m for m in unique_matches if
                        any(nt in m["home_team"].lower() or nt in m["away_team"].lower()
                            for nt in national_teams_lower)]
            others = [m for m in unique_matches if m not in relevant]
            unique_matches = relevant + others
        if unique_matches:
            match_str = "\n".join([
                f"- {m['date']}: {m['home_team']} vs {m['away_team']} ({m['competition']})"
                for m in unique_matches[:10]
            ])
            api_parts.append(f"Upcoming Matches:\n{match_str}")
        else:
            api_parts.append("No upcoming matches found for the specified criteria.")

    # Recent Match Results (for context/form analysis)
    if intent.get("needs_api_recent_matches"):
        league_codes_to_check = intent["league_mentions"] if intent["league_mentions"] else []
        for lc in league_codes_to_check[:2]:
            recent = api.get_recent_matches(lc, days_back=14)
            if recent:
                # Filter to teams mentioned if possible
                national_teams_lower = intent.get("mentioned_national_teams", [])
                if national_teams_lower:
                    recent = [m for m in recent if
                              any(nt in m["home_team"].lower() or nt in m["away_team"].lower()
                                  for nt in national_teams_lower)]
                if recent:
                    result_str = "\n".join([
                        f"- {m['date']}: {m['home_team']} {m['home_score']}-{m['away_score']} {m['away_team']} ({m['competition']})"
                        for m in recent[:8]
                    ])
                    api_parts.append(f"Recent Results (last 14 days):\n{result_str}")

    # Club team standings search (from KB-confirmed teams)
    if intent["needs_api_team_search"] and found_teams:
        for team_name in found_teams:
            teams = api.search_team_in_standings(team_name)
            if teams:
                t = teams[0]
                api_parts.append(f"Current Form for {t['team']} ({t['league']}): Pos {t['position']}, {t['points']} pts. GD: {t['goal_diff']}.")
                break  # max 1 to save API quota

    # --- Web Search Context (Tavily) ---
    # Triggered for match analysis, injuries, odds, lineups, team news, or any team mention
    if intent.get("needs_web_search") and ws.is_web_search_configured():
        national_teams = intent.get("mentioned_national_teams", [])

        if len(national_teams) >= 2:
            # Two teams detected — search for match preview + injuries (NOT odds, covered by Odds API)
            home, away = national_teams[0].title(), national_teams[1].title()
            preview = ws.search_match_preview(home, away, "FIFA World Cup 2026")
            if preview:
                api_parts.append(preview)
        elif len(national_teams) == 1:
            # One team — search for team news
            team = national_teams[0].title()
            news = ws.search_team_news(team)
            if news:
                api_parts.append(news)
        else:
            # General query — do a direct search with the original query
            results = ws.search_web(query + " football betting 2026", max_results=4)
            if results:
                api_parts.append(ws._format_results(results, "Web Search Results"))

    # --- The Odds API — Real bookmaker odds ---
    if odds_api.is_configured():
        national_teams = intent.get("mentioned_national_teams", [])
        if len(national_teams) >= 2:
            home, away = national_teams[0].title(), national_teams[1].title()
            game = odds_api.find_match_odds(home, away)
            if game:
                odds_str = odds_api.format_odds_for_llm(game)
                if odds_str:
                    api_parts.append(odds_str)
        elif intent.get("needs_api_upcoming_matches") and not intent.get("mentioned_national_teams"):
            # General upcoming matches query — show WC odds overview
            wc_games = odds_api.get_wc_odds()
            if wc_games:
                overview = ["Live Odds Overview (FIFA World Cup 2026):"]
                for g in wc_games[:5]:
                    h2h = g.get("h2h")
                    if h2h:
                        overview.append(
                            f"  {g['home_team']} vs {g['away_team']} ({g['date']}): "
                            f"{g['home_team']} {h2h['home']} | Draw {h2h['draw']} | {g['away_team']} {h2h['away']}"
                        )
                if len(overview) > 1:
                    api_parts.append("\n".join(overview))

    # Format output
    kb_context = "\n\n".join(kb_parts) if kb_parts else ""
    api_context = "\n\n".join(api_parts) if api_parts else ""

    # Truncate if too long (simple protection)
    if len(kb_context) > 3000:
        kb_context = kb_context[:3000] + "...\n(Truncated)"
    if len(api_context) > 5000:
        api_context = api_context[:5000] + "...\n(Truncated)"

    return kb_context, api_context
