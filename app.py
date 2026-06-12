import streamlit as st
import os

st.set_page_config(page_title="BetAssist AI", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.chat import render_chat_ui
from components.match_card import render_match_card
from modules.knowledge_base import init_db, get_all_strategies, get_all_terms
from modules.football_api import get_upcoming_matches, get_standings, AVAILABLE_LEAGUES


if "db_initialized" not in st.session_state:
    init_db()
    from modules.seed_data import seed_knowledge_base, is_seeded

    if not is_seeded(): seed_knowledge_base()
    st.session_state["db_initialized"] = True

render_sidebar()
active_page = render_navbar()

# =====================================================================
# 1. WARUNKOWY INPUT CZATU (PRZENIESIONY NA GÓRĘ!)
# =====================================================================
# Dzięki temu, że input jest tutaj, Streamlit NATYCHMIAST wysyła do
# przeglądarki rozkaz jego usunięcia, zanim zablokuje się na API!
prompt = None
if active_page == "💬 Chat":
    is_generating = st.session_state.get("is_generating", False)
    prompt = st.chat_input("E.g., What is Asian Handicap?", disabled=is_generating)

# =====================================================================
# 2. GŁÓWNY VIEWPORT (Wyświetlanie treści)
# =====================================================================
main_viewport = st.container(height=600, border=False)

with main_viewport:
    if active_page == "💬 Chat":
        st.markdown("Ask me about betting strategies, team form, upcoming matches, or terminology.")
        render_chat_ui()

    elif active_page == "⚽ Upcoming Matches":
        st.subheader("Upcoming Matches")
        league_selection = st.selectbox("Select League:", options=[None] + list(AVAILABLE_LEAGUES.keys()),
                                        format_func=lambda
                                            x: "All Leagues" if x is None else f"{AVAILABLE_LEAGUES[x]['emoji']} {AVAILABLE_LEAGUES[x]['name']}")

        if st.button("🔄 Refresh Matches"):
            st.cache_data.clear()

        # Pokaże się natychmiast po zniknięciu czatu!
        with st.spinner("Fetching upcoming matches from API..."):
            matches = get_upcoming_matches(league_selection, days_ahead=5)
            if not matches:
                st.info("No upcoming matches found.")
            else:
                cols = st.columns(2)
                for i, match in enumerate(matches[:20]):
                    with cols[i % 2]: render_match_card(match)

    elif active_page == "📊 Standings":
        st.subheader("League Standings")
        col1, col2 = st.columns([1, 3])
        with col1:
            standings_league = st.selectbox("Select League:", options=list(AVAILABLE_LEAGUES.keys()), format_func=lambda
                x: f"{AVAILABLE_LEAGUES[x]['emoji']} {AVAILABLE_LEAGUES[x]['name']}", key="standings_league_select")

        with col2:
            # Pokaże się natychmiast po zniknięciu czatu!
            with st.spinner("Fetching live standings..."):
                standings = get_standings(AVAILABLE_LEAGUES[standings_league]["code"])
                if standings:
                    st.dataframe(standings, hide_index=True, use_container_width=True)
                else:
                    st.warning("Could not fetch standings for this league. The API rate limit may have been reached.")

    elif active_page == "📚 Knowledge Base":
        st.subheader("Browse Knowledge Base")
        st.write("This is the custom domain knowledge injected into the AI.")
        kb_tab1, kb_tab2, kb_tab3 = st.tabs(["Strategies", "Terminology", "📋 My Rules"])

        with kb_tab1:
            for s in get_all_strategies():
                with st.expander(f"{s['name']}  —  Risk: {s['risk_level'].upper()}"):
                    st.markdown(
                        f"**Category:** {s['category']}\n\n**Description:** {s['description']}\n\n**Example:** _{s['example']}_")
        with kb_tab2:
            for t in get_all_terms():
                st.markdown(f"**{t['term']}**\n- {t['definition']}\n- *Example: {t['example_usage']}*\n---")
        with kb_tab3:
            from modules.rules_loader import list_rule_files, get_rules_dir, invalidate_cache

            st.info(f"Drop your **Markdown (.md)** files into:\n\n`{get_rules_dir()}`")
            if st.button("🔄 Reload Rules Now"): invalidate_cache()
            rule_files = list_rule_files()
            if rule_files:
                for rf in rule_files:
                    with st.expander(f"📄 {rf['filename']}"):
                        with open(rf["path"], encoding="utf-8") as f: st.markdown(f.read())

# =====================================================================
# 3. OBSŁUGA WYSŁANIA WIADOMOŚCI
# =====================================================================
if prompt and active_page == "💬 Chat":
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.is_generating = True
    st.rerun()