import streamlit as st
from modules.llm import get_chat_stream
from modules.query_router import get_context_for_query, classify_intent

# --- Słownik kolorów i helpery od kumpla ---
_SOURCE_COLOURS = {
    "kb": ("#6366f1", "📚 Knowledge Base"),
    "api": ("#10b981", "⚽ Football API"),
    "elo": ("#f59e0b", "📊 ELO Ratings"),
    "odds": ("#3b82f6", "💰 Odds API"),
    "web": ("#ef4444", "🌐 Web Search"),
}


def _source_badges(kb_context: str, api_context: str) -> str:
    """Build HTML source-tag pills showing which data sources contributed."""
    used = []
    if kb_context:
        used.append(_SOURCE_COLOURS["kb"])
    if "ELO World Rankings" in api_context:
        used.append(_SOURCE_COLOURS["elo"])
    if "Upcoming Matches" in api_context or "Recent Results" in api_context:
        used.append(_SOURCE_COLOURS["api"])
    if "bookmaker" in api_context.lower() or "Pinnacle" in api_context or "Betfair" in api_context:
        used.append(_SOURCE_COLOURS["odds"])
    if "Web Search" in api_context:
        used.append(_SOURCE_COLOURS["web"])

    if not used:
        return ""

    pills = " ".join(
        f'<span style="background:{colour};color:white;padding:2px 8px;'
        f'border-radius:999px;font-size:0.72rem;margin-right:4px;">{label}</span>'
        for colour, label in used
    )
    return f'<div style="margin-top:6px;margin-bottom:2px">{pills}</div>'


def _intent_label(intent_type: str) -> str:
    labels = {
        "MATCH": "🔍 Analyzing match",
        "ODDS": "💰 Analyzing odds",
        "TERM": "📖 Looking up term",
        "TABLE": "📊 Fetching standings",
        "GENERAL": "💬 Processing query",
    }
    return labels.get(intent_type, "⚙️ Processing")


# --- Główna funkcja renderująca (Twoja architektura) ---
def render_chat():
    """Renders the main chat interface."""

    # Tytuł sekcji (bez st.header, bo mamy już globalny w navbarze)
    st.markdown("Ask me about betting strategies, team form, upcoming matches, or terminology.")

    # 1. Inicjalizacja sesji (Bogatsze powitanie od kumpla)
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": (
                "Hello! I'm **BetAssist AI**. I can help you:\n"
                "- ⚽ Analyze upcoming matches with live ELO ratings & odds\n"
                "- 📖 Explain betting strategies and terminology\n"
                "- 📊 Look up league standings and team form\n\n"
                "What would you like to know?"
            )
        }]
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    # 2. Kontener na historię czatu (Twój sztywny layout chroniący stronę przed skakaniem)
    chat_area = st.container(height=450, border=False)

    with chat_area:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Renderowanie zapisanych badge'y źródłowych (od kumpla)
                if message["role"] == "assistant" and message.get("source_html"):
                    st.markdown(message["source_html"], unsafe_allow_html=True)

    # 3. Input bota (Zablokowany podczas pracy!)
    prompt = st.chat_input("E.g., What is Asian Handicap?", disabled=st.session_state.is_generating)

    # 4. Obsługa wpisania nowej wiadomości
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_generating = True
        st.rerun()

    # 5. Logika generowania (uruchamia się po odświeżeniu lub przycisku "Analyze" z innej zakładki)
    if st.session_state.is_generating:
        # Pobieramy ostatnią wiadomość użytkownika z historii
        last_user_msg = st.session_state.messages[-1]["content"]

        with chat_area:
            # Pasek postępu (Zastępuje Twojego zwykłego spinnera)
            with st.status("Analyzing your query...", expanded=True) as status:

                # Etap 1: Intencje
                status.update(label="🧠 Classifying query intent...")
                try:
                    intent_type = classify_intent(last_user_msg)
                    intent_label = _intent_label(intent_type)
                except Exception:
                    intent_label = _intent_label("GENERAL")
                status.update(label=f"{intent_label}...")

                # Etap 2: Baza wiedzy i API
                status.update(label="📚 Searching knowledge base and API...")
                try:
                    kb_context, api_context = get_context_for_query(last_user_msg)
                except Exception as e:
                    kb_context, api_context = "", ""
                    st.warning(f"Context retrieval issue: {e}")

                # Zwijamy status, gdy kończy zbierać dane
                status.update(label="✅ Context retrieved. Generating response...", state="complete", expanded=False)

            # Właściwa odpowiedź AI
            with st.chat_message("assistant"):
                try:
                    stream = get_chat_stream(
                        user_message=last_user_msg,
                        chat_history=st.session_state.messages[:-1],
                        kb_context=kb_context,
                        api_context=api_context
                    )
                    response = st.write_stream(stream)
                except Exception as e:
                    response = f"⚠️ Error: {str(e)}"
                    st.markdown(response)

                # Generowanie kolorowych badge'y ze źródłami
                source_html = _source_badges(kb_context, api_context)
                if source_html:
                    st.markdown(source_html, unsafe_allow_html=True)

                # Rozszerzony, 2-kolumnowy expander debugowania od kumpla
                with st.expander("🔍 View Retrieved Context", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**📚 Knowledge Base**")
                        st.text(kb_context if kb_context else "—")
                    with col2:
                        st.markdown("**⚽ Live Data**")
                        st.text(api_context if api_context else "—")

        # 6. Zapisanie do historii z uwzględnieniem stylów HTML
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "source_html": source_html if source_html else ""
        })

        # Zdjęcie blokady inputu
        st.session_state.is_generating = False
        st.rerun()