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
import modules.elo_ratings as elo_ratings

# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

# Intent types returned by the LLM classifier
# MATCH   — user asks about a specific match, form, prediction, analysis
# ODDS    — user asks about betting odds, value bets, tips
# TERM    — user asks what something means, strategy explanations
# TABLE   — user asks about league tables, standings, rankings
# GENERAL — anything else (greetings, off-topic, etc.)
INTENT_TYPES = {"MATCH", "ODDS", "TERM", "TABLE", "GENERAL"}

_CLASSIFIER_SYSTEM = """You are an intent classifier for a football betting assistant.
Classify the user message into EXACTLY ONE of these categories:
  MATCH  — asks about a specific match, team form, head-to-head, prediction, analysis, injuries, lineups
  ODDS   — asks about betting odds, value bets, tips, best bet, should I bet
  TERM   — asks what a term means, how a strategy works, glossary, education
  TABLE  — asks about league standings, rankings, points table, top scorers
  GENERAL — anything else: greetings, off-topic, vague questions

Reply with ONLY one word from the list above. No punctuation, no explanation."""


def classify_intent(query: str) -> str:
    """
    Use a lightweight Gemini call to classify the query intent.
    Returns one of: MATCH | ODDS | TERM | TABLE | GENERAL.
    Falls back to keyword heuristic on error (no extra latency impact).
    """
    try:
        from modules.llm import get_llm
        llm = get_llm()
        if not llm:
            return _classify_heuristic(query)
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke(
            [SystemMessage(content=_CLASSIFIER_SYSTEM),
             HumanMessage(content=query[:400])],  # trim to save tokens
        )
        result = response.content.strip().upper().split()[0] if response.content else ""
        return result if result in INTENT_TYPES else _classify_heuristic(query)
    except Exception:
        return _classify_heuristic(query)


def _classify_heuristic(query: str) -> str:
    """Fast keyword-based fallback classifier (no network needed)."""
    q = query.lower()
    if any(w in q for w in ["standing", "table", "rank", "position", "points", "leader"]):
        return "TABLE"
    if any(w in q for w in ["what is", "explain", "meaning", "definition", "how does", "strategy", "strategies",
                             "handicap", "asian", "over", "under", "btts", "accumulator", "parlay", "kelly",
                             "bankroll", "ev", "roi", "arbitrage", "matched betting"]):
        return "TERM"
    if any(w in q for w in ["odds", "kurs", "value bet", "tip", "should i bet", "best bet", "typowanie"]):
        return "ODDS"
    if any(w in q for w in ["match", "game", "predict", "analysis", "form", "h2h", "head to head",
                             "injury", "lineup", "squad", "vs", "versus", "upcoming", "fixture",
                             "prognoz", "analiz", "preview"]):
        return "MATCH"
    return "GENERAL"

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

    # --- LLM-based intent classification (fast single-token call) ---
    intent_type = classify_intent(query)

    intent = {
        "intent_type": intent_type,
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

    # 1. Terms & strategies — only for TERM and ODDS intents
    if intent_type in ("TERM", "ODDS") or any(keyword in query_lower for keyword in BETTING_TERMS_KEYWORDS):
        intent["needs_kb_terms"] = True
        intent["needs_kb_strategies"] = True

    # 2. League mentions (always check)
    for league_key, league_info in AVAILABLE_LEAGUES.items():
        if league_info["name"].lower() in query_lower or league_key.lower() in query_lower:
            intent["league_mentions"].append(league_info["code"])
            intent["needs_kb_league_insights"] = True

    # 3. API intents — only for MATCH, ODDS, TABLE (not TERM or GENERAL)
    if intent_type in ("MATCH", "ODDS") or any(word in query_lower for word in
            ["match", "matches", "game", "games", "play", "playing", "weekend",
             "today", "tomorrow", "upcoming", "fixture", "analysis",
             "predict", "prediction", "bet", "betting"]):
        intent["needs_api_upcoming_matches"] = True

    if intent_type == "TABLE" or any(word in query_lower for word in
            ["table", "standings", "rank", "position", "leader", "points"]):
        intent["needs_api_standings"] = True

    # 4. World Cup context
    if any(kw in query_lower for kw in WC_KEYWORDS):
        if 2000 not in intent["league_mentions"]:
            intent["league_mentions"].append(2000)
        intent["needs_api_upcoming_matches"] = True

    # 5. National team detection
    mentioned_national_teams = [t for t in NATIONAL_TEAMS if t in query_lower]
    intent["mentioned_national_teams"] = mentioned_national_teams
    if mentioned_national_teams:
        if 2000 not in intent["league_mentions"]:
            intent["league_mentions"].append(2000)
        intent["needs_api_upcoming_matches"] = True
        intent["needs_api_recent_matches"] = True
    else:
        intent["needs_api_recent_matches"] = False

    # 6. Web search — only for MATCH and ODDS intents
    intent["needs_web_search"] = bool(
        intent_type in ("MATCH", "ODDS")
        and (
            mentioned_national_teams
            or any(w in query_lower for w in [
                "injur", "lineup", "squad", "suspend", "absent", "miss",
                "odds", "kurs", "typowanie", "prognoz", "analiz", "preview",
                "predict", "news", "form", "head to head", "h2h",
            ])
            or intent["needs_api_upcoming_matches"]
        )
    )

    # 7. Club team notes — only for MATCH and ODDS intents (was always True — bug fixed)
    if intent_type in ("MATCH", "ODDS"):
        intent["needs_kb_team_notes"] = True
        intent["needs_api_team_search"] = True
    else:
        intent["needs_kb_team_notes"] = False
        intent["needs_api_team_search"] = False

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

    # --- ELO Ratings (eloratings.net) ---
    # Build a unified list of team names to look up: national teams from query
    # + any club teams resolved via Knowledge Base.
    teams_to_lookup = []

    national_teams_detected = intent.get("mentioned_national_teams", [])
    if national_teams_detected:
        teams_to_lookup.extend([t.title() for t in national_teams_detected])

    # Also add club teams found via KB (found_teams may be empty for national-only queries)
    for club in found_teams:
        teams_to_lookup.append(club)

    if teams_to_lookup:
        elo_str = elo_ratings.format_elo_for_llm(teams_to_lookup)
        if elo_str:
            api_parts.append(elo_str)

    # Format output
    kb_context = "\n\n".join(kb_parts) if kb_parts else ""
    api_context = "\n\n".join(api_parts) if api_parts else ""

    # Truncate if too long (simple protection)
    if len(kb_context) > 3000:
        kb_context = kb_context[:3000] + "...\n(Truncated)"
    if len(api_context) > 5000:
        api_context = api_context[:5000] + "...\n(Truncated)"

    return kb_context, api_context
