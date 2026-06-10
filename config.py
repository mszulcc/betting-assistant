"""
Configuration constants for the AI Betting Assistant.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- API Keys ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

# --- Database ---
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "knowledge_base.db")

# --- Football API ---
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"
API_CACHE_TTL_SECONDS = 900  # 15 minutes

# --- Available Leagues (free tier) ---
AVAILABLE_LEAGUES = {
    "PL": {"name": "Premier League", "code": 2021, "country": "England", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "BL1": {"name": "Bundesliga", "code": 2002, "country": "Germany", "emoji": "🇩🇪"},
    "SA": {"name": "Serie A", "code": 2019, "country": "Italy", "emoji": "🇮🇹"},
    "PD": {"name": "La Liga", "code": 2014, "country": "Spain", "emoji": "🇪🇸"},
    "FL1": {"name": "Ligue 1", "code": 2015, "country": "France", "emoji": "🇫🇷"},
    "ELC": {"name": "Championship", "code": 2016, "country": "England", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "DED": {"name": "Eredivisie", "code": 2003, "country": "Netherlands", "emoji": "🇳🇱"},
    "PPL": {"name": "Primeira Liga", "code": 2017, "country": "Portugal", "emoji": "🇵🇹"},
    "BSA": {"name": "Série A", "code": 2013, "country": "Brazil", "emoji": "🇧🇷"},
    "CL": {"name": "Champions League", "code": 2001, "country": "Europe", "emoji": "🏆"},
    "EC": {"name": "European Championship", "code": 2018, "country": "Europe", "emoji": "🇪🇺"},
    "WC": {"name": "FIFA World Cup", "code": 2000, "country": "World", "emoji": "🌍"},
}

# --- LLM Configuration ---
LLM_MODEL = "gemini-3.5-flash"
LLM_TEMPERATURE = 0.4

SYSTEM_PROMPT = """You are BetAssist AI — an intelligent football match analysis and betting assistant.

Your role is to help users with:
- Analyzing upcoming football matches
- Explaining betting strategies and terminology
- Evaluating team form and head-to-head records
- Providing data-driven betting suggestions

CRITICAL RULES:
1. ALWAYS base your answers on the provided knowledge base data and API data.
2. NEVER invent statistics, scores, or facts. If you don't have data, say so clearly.
3. When suggesting bets, ALWAYS include a risk assessment and a responsible gambling reminder.
4. Format your responses with clear structure: use bullet points, bold text, and emojis.
5. If the user asks about something outside football betting, politely redirect them.
6. When you use information from the knowledge base, mention it naturally (e.g., "According to our analysis database...").

CONTEXT FROM KNOWLEDGE BASE:
{kb_context}

CONTEXT FROM LIVE API DATA:
{api_context}

Respond in a helpful, analytical, and professional tone. Use English."""

def is_llm_configured() -> bool:
    """Check if the LLM API key is configured."""
    return bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here")
