"""
Match Analyzer module.
Combines API data and Knowledge Base data to create a comprehensive
match analysis payload, ready for LLM processing or UI display.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import modules.football_api as api
import modules.knowledge_base as kb

def analyze_match(home_team: str, away_team: str, match_id: int = None) -> dict:
    """
    Gather all relevant data for a specific match.
    
    Args:
        home_team: Name of the home team
        away_team: Name of the away team
        match_id: Optional API match ID for fetching H2H data
        
    Returns:
        dict containing structured analysis data
    """
    return {"status": "Analyzer temporarily disabled."}
    
    analysis = {
        "home_team": home_team,
        "away_team": away_team,
        "api_data": {
            "home_standings": None,
            "away_standings": None,
            "h2h": None,
        },
        "kb_data": {
            "home_notes": None,
            "away_notes": None,
            "relevant_tips": []
        }
    }

    # --- 1. Fetch Live API Data ---
    home_standings = api.search_team_in_standings(home_team)
    if home_standings:
        analysis["api_data"]["home_standings"] = home_standings[0]
        
    away_standings = api.search_team_in_standings(away_team)
    if away_standings:
        analysis["api_data"]["away_standings"] = away_standings[0]

    if match_id:
        analysis["api_data"]["h2h"] = api.get_head_to_head(match_id)

    # --- 2. Fetch Knowledge Base Data ---
    home_notes = kb.search_team_notes(home_team)
    if home_notes:
        analysis["kb_data"]["home_notes"] = home_notes[0]
        
    away_notes = kb.search_team_notes(away_team)
    if away_notes:
        analysis["kb_data"]["away_notes"] = away_notes[0]

    # Search for historical tips involving these teams
    tips_query = f"{home_team} {away_team}"
    tips = kb.search_historical_tips(tips_query, limit=3)
    if tips:
        analysis["kb_data"]["relevant_tips"] = tips

    return analysis

def format_analysis_for_llm(analysis: dict) -> str:
    """Format the structured analysis dict into a text string for the LLM prompt."""
    parts = []
    
    home = analysis["home_team"]
    away = analysis["away_team"]
    
    parts.append(f"MATCH ANALYSIS REQUEST: {home} vs {away}\n")
    
    # Standings
    h_std = analysis["api_data"]["home_standings"]
    a_std = analysis["api_data"]["away_standings"]
    
    parts.append("--- CURRENT STANDINGS (API) ---")
    if h_std:
        parts.append(f"{home}: Pos {h_std['position']} in {h_std['league']}, {h_std['points']} pts, Goal Diff {h_std['goal_diff']}")
    else:
        parts.append(f"{home}: Standings not found.")
        
    if a_std:
        parts.append(f"{away}: Pos {a_std['position']} in {a_std['league']}, {a_std['points']} pts, Goal Diff {a_std['goal_diff']}")
    else:
        parts.append(f"{away}: Standings not found.")
        
    # H2H
    h2h = analysis["api_data"]["h2h"]
    if h2h:
        parts.append("\n--- HEAD-TO-HEAD (API) ---")
        parts.append(f"Total Matches: {h2h['total_matches']}")
        parts.append(f"{home} Wins: {h2h['home_wins']} | {away} Wins: {h2h['away_wins']} | Draws: {h2h['draws']}")
        
    # Team Notes
    h_notes = analysis["kb_data"]["home_notes"]
    a_notes = analysis["kb_data"]["away_notes"]
    
    parts.append("\n--- EXPERT TEAM NOTES (KNOWLEDGE BASE) ---")
    if h_notes:
        parts.append(f"{home} Strengths: {h_notes['strengths']}")
        parts.append(f"{home} Weaknesses: {h_notes['weaknesses']}")
        parts.append(f"{home} Form: {h_notes['form_notes']}")
        
    if a_notes:
        parts.append(f"{away} Strengths: {a_notes['strengths']}")
        parts.append(f"{away} Weaknesses: {a_notes['weaknesses']}")
        parts.append(f"{away} Form: {a_notes['form_notes']}")
        
    # Historical Tips
    tips = analysis["kb_data"]["relevant_tips"]
    if tips:
        parts.append("\n--- HISTORICAL BETTING TIPS (KNOWLEDGE BASE) ---")
        for t in tips:
            parts.append(f"Match: {t['match_description']}")
            parts.append(f"Prediction: {t['prediction']} (Odds: {t['odds_taken']})")
            parts.append(f"Result: {t['result']}")
            parts.append(f"Reasoning: {t['reasoning']}\n")
            
    parts.append("\nINSTRUCTIONS FOR LLM:")
    parts.append("Based on the data above, provide a comprehensive betting analysis for this match. Suggest 1-2 potential bets, assess the risk level, and clearly explain your reasoning based on the provided data. Do not invent data.")
    
    return "\n".join(parts)
