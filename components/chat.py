import streamlit as st
from modules.llm import get_chat_stream
from modules.query_router import get_context_for_query, classify_intent

# Source badge colours by data provider
_SOURCE_COLOURS = {
    "kb":       ("#6366f1", "📚 Knowledge Base"),
    "api":      ("#10b981", "⚽ Football API"),
    "elo":      ("#f59e0b", "📊 ELO Ratings"),
    "odds":     ("#3b82f6", "💰 Odds API"),
    "web":      ("#ef4444", "🌐 Web Search"),
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
        "MATCH":   "🔍 Analyzing match",
        "ODDS":    "💰 Analyzing odds",
        "TERM":    "📖 Looking up term",
        "TABLE":   "📊 Fetching standings",
        "GENERAL": "💬 Processing query",
    }
    return labels.get(intent_type, "⚙️ Processing")


def render_chat(prompt=None):
    """Renders the main chat interface."""
    st.header("💬 Chat with BetAssist AI")
    st.markdown("Ask me about betting strategies, team form, upcoming matches, or terminology.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Hello! I'm **BetAssist AI**. I can help you:\n"
                "- ⚽ Analyze upcoming matches with live ELO ratings & odds\n"
                "- 📖 Explain betting strategies and terminology\n"
                "- 📊 Look up league standings and team form\n\n"
                "What would you like to know?"
            ),
        })

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Re-render source badges stored in message metadata
            if message["role"] == "assistant" and message.get("source_html"):
                st.markdown(message["source_html"], unsafe_allow_html=True)

    # React to user input
    if prompt:
        # Display user message immediately
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        kb_context = ""
        api_context = ""

        # ----------------------------------------------------------------
        # Multi-step progress indicator
        # ----------------------------------------------------------------
        with st.status("Analyzing your query...", expanded=True) as status:

            # Step 1: Classify intent
            status.update(label="🧠 Classifying query intent...")
            intent_type = classify_intent(prompt)
            intent_label = _intent_label(intent_type)
            status.update(label=f"{intent_label}...")

            # Step 2: Knowledge Base
            status.update(label="📚 Searching knowledge base...")
            try:
                kb_context, api_context = get_context_for_query(prompt)
            except Exception as e:
                kb_context, api_context = "", ""
                st.warning(f"Context retrieval issue: {e}")

            # Step 3: Generating response (will stream below)
            status.update(label="🤖 Generating AI response...", state="running")

        # ----------------------------------------------------------------
        # Stream LLM response
        # ----------------------------------------------------------------
        with st.chat_message("assistant"):
            try:
                stream = get_chat_stream(
                    user_message=prompt,
                    chat_history=st.session_state.messages[:-1],
                    kb_context=kb_context,
                    api_context=api_context,
                )
                response = st.write_stream(stream)
            except Exception as e:
                response = f"⚠️ An error occurred while generating your response: {str(e)}"
                st.markdown(response)

            # Source badges
            source_html = _source_badges(kb_context, api_context)
            if source_html:
                st.markdown(source_html, unsafe_allow_html=True)

            # Collapsible raw context (debug)
            with st.expander("🔍 View Retrieved Context", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📚 Knowledge Base**")
                    st.text(kb_context if kb_context else "—")
                with col2:
                    st.markdown("**⚽ Live Data**")
                    st.text(api_context if api_context else "—")

        # Persist message with source metadata
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "source_html": source_html if source_html else "",
        })

        st.rerun()