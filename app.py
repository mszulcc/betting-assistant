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
from components.chat import render_chat
from components.match_card import render_match_card
from modules.knowledge_base import init_db, get_all_strategies, get_all_terms
from modules.football_api import get_upcoming_matches, get_standings, AVAILABLE_LEAGUES

# Inicjalizacja bazy danych przy pierwszym uruchomieniu
init_db()

# Seed KB with starter data if empty (runs only once)
from modules.seed_data import seed_knowledge_base, is_seeded
if not is_seeded():
    seed_knowledge_base()


# Renderowanie paska bocznego
render_sidebar()

# 4. Definicja zakładek interfejsu
tab_chat, tab_matches, tab_standings, tab_kb = st.tabs([
    "💬 Chat", 
    "⚽ Upcoming Matches", 
    "📊 Standings", 
    "📚 Knowledge Base"
])

# 5. Przechwytywanie inputu użytkownika na samym dole struktury kodu (Globalnie)
# Dzięki temu pole tekstowe jest na stałe zakotwiczone na dole ekranu.
prompt = st.chat_input("E.g., What is Asian Handicap? or How is Liverpool's form?")

# 6. Renderowanie zawartości poszczególnych zakładek
with tab_chat:
    # Przekazujemy przechwycony prompt bezpośrednio do komponentu czatu
    render_chat(prompt)

with tab_matches:
    st.header("⚽ Upcoming Matches")
    st.write("Browse upcoming matches and click 'Analyze' to have the AI generate a betting preview.")
    
    league_selection = st.selectbox(
        "Select League:", 
        options=[None] + list(AVAILABLE_LEAGUES.keys()),
        format_func=lambda x: "All Leagues" if x is None else f"{AVAILABLE_LEAGUES[x]['emoji']} {AVAILABLE_LEAGUES[x]['name']}"
    )
    
    if st.button("🔄 Refresh Matches"):
        st.cache_data.clear()
        
    with st.spinner("Fetching matches..."):
        matches = get_upcoming_matches(league_selection, days_ahead=5)
        
        if not matches:
            st.info("No upcoming matches found for the selected criteria.")
        else:
            # Wyświetlanie meczów w siatce dwukolumnowej
            cols = st.columns(2)
            for i, match in enumerate(matches[:20]): # Limit do 20 meczów, aby uniknąć przeciążenia interfejsu
                with cols[i % 2]:
                    render_match_card(match)

with tab_standings:
    st.header("📊 League Standings")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        standings_league = st.selectbox(
            "Select League for Standings:", 
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
                        "league": None # ukryj kolumnę z nazwą ligi
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("Could not fetch standings for this league. The API rate limit may have been reached or the league is not supported in the free tier.")

with tab_kb:
    st.header("📚 Browse Knowledge Base")
    st.write("This is the custom domain knowledge injected into the AI.")

    kb_tab1, kb_tab2, kb_tab3 = st.tabs(["Strategies", "Terminology", "📋 My Rules"])

    with kb_tab1:
        st.subheader("Betting Strategies")
        strategies = get_all_strategies()
        for s in strategies:
            with st.expander(f"{s['name']}  —  Risk: {s['risk_level'].upper()}"):
                st.markdown(f"**Category:** {s['category']}")
                st.markdown(f"**Description:** {s['description']}")
                st.markdown(f"**Example:** _{s['example']}_")

    with kb_tab2:
        st.subheader("Glossary of Terms")
        terms = get_all_terms()
        for t in terms:
            st.markdown(f"**{t['term']}**")
            st.markdown(f"- {t['definition']}")
            st.markdown(f"- *Example: {t['example_usage']}*")
            st.markdown("---")

    with kb_tab3:
        from modules.rules_loader import list_rule_files, get_rules_dir, has_rules, invalidate_cache

        st.subheader("📋 My Betting Rules")
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
            st.warning(
                "No rule files found yet. Add a `.md` file to the rules folder shown above."
            )
        else:
            st.success(f"{len(rule_files)} rule file(s) loaded and active in every AI response.")
            for rf in rule_files:
                with st.expander(f"📄 {rf['filename']}  —  {rf['size_kb']} KB  |  Modified: {rf['modified']}"):
                    try:
                        with open(rf["path"], encoding="utf-8") as f:
                            st.markdown(f.read())
                    except Exception as e:
                        st.error(f"Could not read file: {e}")