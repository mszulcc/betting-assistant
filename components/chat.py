import streamlit as st
from modules.llm import get_chat_stream
from modules.query_router import get_context_for_query

def render_chat():
    """Renders the main chat interface."""

    # Tytuł sekcji (bez CSS, bo jest już w navbarze)
    st.markdown("Ask me about betting strategies, team form, upcoming matches, or terminology.")

    # Inicjalizacja sesji
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm BetAssist AI..."}]
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    # Kontener na historię czatu (scrollowany)
    chat_area = st.container(height=450, border=False)

    with chat_area:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input bota
    prompt = st.chat_input("E.g., What is Asian Handicap?", disabled=st.session_state.is_generating)

    # ... (Tutaj reszta Twojej logiki przetwarzania if prompt: ... bez zmian)

    # 5. Logika przetwarzania
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_generating = True
        st.rerun()

    if st.session_state.is_generating:
        with chat_area:
            with st.spinner("Analyzing data..."):
                try:
                    kb_context, api_context = "", ""
                except Exception as e:
                    kb_context, api_context = "", ""
                    st.error(f"Context retrieval error: {e}")

            with st.chat_message("assistant"):
                try:
                    stream = get_chat_stream(
                        user_message=st.session_state.messages[-1]["content"],
                        chat_history=st.session_state.messages[:-1],
                        kb_context=kb_context,
                        api_context=api_context
                    )
                    response = st.write_stream(stream)
                except Exception as e:
                    response = f"⚠️ Error: {str(e)}"
                    st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.is_generating = False
        st.rerun()