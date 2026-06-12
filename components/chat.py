import streamlit as st
from modules.llm import get_chat_stream
from modules.query_router import get_context_for_query, classify_intent

_SOURCE_COLOURS = {
    "kb": ("#6366f1", "📚 Knowledge Base"),
    "api": ("#10b981", "⚽ Football API"),
    "elo": ("#f59e0b", "📊 ELO Ratings"),
    "odds": ("#3b82f6", "💰 Odds API"),
    "web": ("#ef4444", "🌐 Web Search"),
}


def _source_badges(kb_context: str, api_context: str) -> str:
    used = []
    if kb_context: used.append(_SOURCE_COLOURS["kb"])
    if "ELO World Rankings" in api_context: used.append(_SOURCE_COLOURS["elo"])
    if "Upcoming Matches" in api_context or "Recent Results" in api_context: used.append(_SOURCE_COLOURS["api"])
    if "bookmaker" in api_context.lower() or "Pinnacle" in api_context or "Betfair" in api_context: used.append(
        _SOURCE_COLOURS["odds"])
    if "Web Search" in api_context: used.append(_SOURCE_COLOURS["web"])
    if not used: return ""
    pills = " ".join(
        f'<span style="background:{c};color:white;padding:2px 8px;border-radius:999px;font-size:0.72rem;margin-right:4px;">{l}</span>'
        for c, l in used)
    return f'<div style="margin-top:6px;margin-bottom:2px">{pills}</div>'


def _intent_label(intent_type: str) -> str:
    labels = {"MATCH": "🔍 Analyzing match", "ODDS": "💰 Analyzing odds", "TERM": "📖 Looking up term",
              "TABLE": "📊 Fetching standings", "GENERAL": "💬 Processing query"}
    return labels.get(intent_type, "⚙️ Processing")


def render_chat_ui():
    """Renders ONLY the chat messages and handles the LLM generation."""

    # 1. Inicjalizacja sesji
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! I'm **BetAssist AI**. I can help you analyze matches, explain betting strategies, or look up team stats. What would you like to know?"
        }]
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    # 2. Renderowanie historii
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("source_html"):
                st.markdown(message["source_html"], unsafe_allow_html=True)

    # 3. Logika generowania (uruchamiana z app.py)
    if st.session_state.is_generating:
        last_user_msg = st.session_state.messages[-1]["content"]

        # Ozdobny status od kumpla
        with st.status("Analyzing your query...", expanded=True) as status:
            status.update(label="🧠 Classifying query intent...")
            try:
                intent_type = classify_intent(last_user_msg)
                intent_label = _intent_label(intent_type)
            except Exception:
                intent_label = _intent_label("GENERAL")
            status.update(label=f"{intent_label}...")

            status.update(label="📚 Searching knowledge base and API...")
            try:
                kb_context, api_context = get_context_for_query(last_user_msg)
            except Exception as e:
                kb_context, api_context = "", ""
                st.warning(f"Context retrieval issue: {e}")

            status.update(label="✅ Context retrieved. Generating response...", state="complete", expanded=False)

        # Strumieniowanie odpowiedzi
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

            source_html = _source_badges(kb_context, api_context)
            if source_html:
                st.markdown(source_html, unsafe_allow_html=True)

            with st.expander("🔍 View Retrieved Context", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📚 Knowledge Base**")
                    st.text(kb_context if kb_context else "—")
                with col2:
                    st.markdown("**⚽ Live Data**")
                    st.text(api_context if api_context else "—")

        # Zapis i zakończenie generowania
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "source_html": source_html if source_html else ""
        })
        st.session_state.is_generating = False
        st.rerun()