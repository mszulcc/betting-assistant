import streamlit as st
import os

# Set page config
st.set_page_config(
    page_title="BetAssist AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Load custom CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# Import components and modules
from components.sidebar import render_sidebar
from components.navbar import render_navbar  # <--- Nasz nowy navbar
from components.chat import render_chat
from components.match_card import render_match_card
from modules.knowledge_base import init_db, get_all_strategies, get_all_terms
from modules.football_api import get_upcoming_matches, get_standings, AVAILABLE_LEAGUES

# Initialize Database on first run
init_db()

# Render Sidebar
render_sidebar()

# Pobieramy to, co użytkownik kliknął w Navbarze
active_page = render_navbar()

# --- SYSTEM ROUTINGU (Zamiast st.tabs) ---

if active_page == "💬 Chat":
    # Teraz render_chat wykonuje się w głównym wątku, więc st.chat_input BĘDZIE DZIAŁAĆ!
    render_chat()

elif active_page == "⚽ Upcoming Matches":
    # ZWIĘKSZONA WYSOKOŚĆ (np. 750), by wykorzystać miejsce po braku czatu
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
    # ZWIĘKSZONA WYSOKOŚĆ
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
                    st.dataframe(standings, hide_index=True, use_container_width=True)

elif active_page == "📚 Knowledge Base":
    # ZWIĘKSZONA WYSOKOŚĆ
    with st.container(height=750, border=False):
        st.subheader("Browse Knowledge Base")

        # O dziwo, tutaj MOŻEMY użyć st.tabs, bo nie ma tu czatu!
        kb_tab1, kb_tab2 = st.tabs(["Strategies", "Terminology"])

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