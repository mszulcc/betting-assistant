import streamlit as st
from modules.llm import get_chat_stream
from modules.query_router import get_context_for_query

def render_chat():
    """Renders the main chat interface."""
    st.header("💬 Chat with BetAssist AI")
    st.markdown("Ask me about betting strategies, team form, upcoming matches, or terminology.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Add a greeting message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm BetAssist AI. I can help you analyze matches, explain betting strategies, or look up team stats. What would you like to know?"
        })

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("E.g., What is Asian Handicap? or How is Liverpool's form?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process the query
        with st.spinner("Analyzing data..."):
            try:
                # 1. Route query to get context (Temporarily disabled)
                # kb_context, api_context = get_context_for_query(prompt)
                kb_context, api_context = "", ""
            except Exception as e:
                kb_context, api_context = "", ""
                st.error(f"Context retrieval error: {e}")
                
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            try:
                # 2. Get LLM stream
                stream = get_chat_stream(
                    user_message=prompt,
                    chat_history=st.session_state.messages[:-1], # Exclude the current message we just added
                    kb_context=kb_context,
                    api_context=api_context
                )
                response = st.write_stream(stream)
            except Exception as e:
                response = f"⚠️ An error occurred while generating your response: {str(e)}"
                st.markdown(response)
            
            # Show expanding box with the retrieved context (for transparency/debugging)
            with st.expander("🔍 View Retrieved Context"):
                st.markdown("### Knowledge Base Context")
                st.text(kb_context if kb_context else "None")
                st.markdown("### API Context")
                st.text(api_context if api_context else "None")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
