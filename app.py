import streamlit as st
import os

# 1. Ustawienia konfiguracji strony (musi być jako pierwsze)
st.set_page_config(
    page_title="BetAssist AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 2. Ładowanie niestandardowych stylów CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# 3. Import komponentów i modułów wewnętrznych
from components.sidebar import render_sidebar
from components.navbar import render_navbar  # <--- Utrzymujemy Twój niezawodny Navbar
from components.chat import render_chat
from components.match_card import render_match_card
from modules.knowledge_base import init_db, get_all_strategies, get_all_terms
from modules.football_api import get_upcoming_matches, get_standings, AVAILABLE_LEAGUES

# --- OPTYMALIZACJA OD KUMPLA: Inicjalizacja i Seeding bazy danych ---
if "db_initialized" not in st.session_state:
    init_db()

    # Seed KB z początkowymi danymi, jeśli baza jest pusta
    from modules.seed_data import seed_knowledge_base, is_seeded

    if not is_seeded():
        seed_knowledge_base()

    st.session_state["db_initialized"] = True

# 4. Renderowanie paska bocznego
render_sidebar()

# 5. Pobieranie aktywnej zakładki z Navbara
active_page = render_navbar()

# --- SYSTEM ROUTINGU (Zamiast st.tabs - zapobiega psuciu UI) ---

if active_page == "💬 Chat":
    # Chat ma własny input zamknięty w komponencie, więc wywołujemy go bez argumentów
    render_chat()

elif active_page == "⚽ Upcoming Matches":
    with st.container(height=750, border=False):
        st.subheader("Upcoming Matches")

        league_selection = st.selectbox(
            "Select League:",
            options=[None] + list(AVAILABLE_LEAGUES.keys()),
            format_func=lambda
                x: "All Leagues" if x is None else f"{AVAILABLE_LEAGUES[x]['emoji']} {AVAILABLE_LEAGUES[x]['name']}"
        )

        if st.button("🔄 Refresh Matches"):
            st.cache_data.clear()

        with st.spinner("Fetching matches..."):
            matches = get_upcoming_matches(league_selection, days_ahead=5)
            if not matches:
                st.info("No upcoming matches found.")
            else:
                cols = st.columns(2)
                for i, match in enumerate(matches[:20]):
                    with cols[i % 2]:
                        render_match_card(match)

elif active_page == "📊 Standings":
    with st.container(height=750, border=False):
        st.subheader("League Standings")

        col1, col2 = st.columns([1, 3])
        with col1:
            standings_league = st.selectbox(
                "Select League:",
                options=list(AVAILABLE_LEAGUES.keys()),
                format_func=lambda x: f"{AVAILABLE_LEAGUES[x]['emoji']} {AVAILABLE_LEAGUES[x]['name']}",
                key="standings_league_select"
            )
        with col2:
            with st.spinner("Fetching standings..."):
                standings = get_standings(AVAILABLE_LEAGUES[standings_league]["code"])
                if standings:
                    st.dataframe(
                        standings,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "position": st.column_config.NumberColumn("Pos"),
                            "team": st.column_config.TextColumn("Team"),
                            "played": st.column_config.NumberColumn("P"),
                            "won": st.column_config.NumberColumn("W"),
                            "draw": st.column_config.NumberColumn("D"),
                            "lost": st.column_config.NumberColumn("L"),
                            "goals_for": st.column_config.NumberColumn("GF"),
                            "goals_against": st.column_config.NumberColumn("GA"),
                            "goal_diff": st.column_config.NumberColumn("GD"),
                            "points": st.column_config.NumberColumn("Pts"),
                            "league": None  # ukryj kolumnę z nazwą ligi
                        }
                    )
                else:
                    st.warning("Could not fetch standings for this league. The API rate limit may have been reached.")

elif active_page == "📚 Knowledge Base":
    with st.container(height=750, border=False):
        st.subheader("Browse Knowledge Base")
        st.write("This is the custom domain knowledge injected into the AI.")

        # --- NOWOŚĆ OD KUMPLA: Trzecia zakładka na zasady (My Rules) ---
        kb_tab1, kb_tab2, kb_tab3 = st.tabs(["Strategies", "Terminology", "📋 My Rules"])

        with kb_tab1:
            st.markdown("#### Betting Strategies")
            strategies = get_all_strategies()
            for s in strategies:
                with st.expander(f"{s['name']}  —  Risk: {s['risk_level'].upper()}"):
                    st.markdown(f"**Category:** {s['category']}")
                    st.markdown(f"**Description:** {s['description']}")
                    st.markdown(f"**Example:** _{s['example']}_")

        with kb_tab2:
            st.markdown("#### Glossary of Terms")
            terms = get_all_terms()
            for t in terms:
                st.markdown(f"**{t['term']}**")
                st.markdown(f"- {t['definition']}")
                st.markdown(f"- *Example: {t['example_usage']}*")
                st.markdown("---")

        with kb_tab3:
            # Integracja modułu ładowania reguł
            from modules.rules_loader import list_rule_files, get_rules_dir, has_rules, invalidate_cache

            st.markdown("#### 📋 My Betting Rules")
            st.info(
                f"Drop your **Markdown (.md)** files into:\n\n"
                f"`{get_rules_dir()}`\n\n"
                "Files are picked up automatically within 60 seconds. "
                "You can have multiple files — they are loaded in alphabetical order."
            )

            col_reload, _ = st.columns([1, 4])
            with col_reload:
                if st.button("🔄 Reload Rules Now"):
                    invalidate_cache()
                    st.success("Rules cache cleared — files will be re-read on next message.")

            rule_files = list_rule_files()

            if not rule_files:
                st.warning("No rule files found yet. Add a `.md` file to the rules folder shown above.")
            else:
                st.success(f"{len(rule_files)} rule file(s) loaded and active in every AI response.")
                for rf in rule_files:
                    with st.expander(f"📄 {rf['filename']}  —  {rf['size_kb']} KB  |  Modified: {rf['modified']}"):
                        try:
                            with open(rf["path"], encoding="utf-8") as f:
                                st.markdown(f.read())
                        except Exception as e:
                            st.error(f"Could not read file: {e}")