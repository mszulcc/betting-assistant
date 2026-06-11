import streamlit as st
import os

def render_sidebar():
    """Renders the Streamlit sidebar with settings and info."""
    with st.sidebar:
        st.title("⚙️ Settings & Info")
        
        st.markdown("### API Configuration")
        st.info("API keys are loaded from the environment (`.env`).")
        
        from config import is_llm_configured
        from modules.football_api import is_api_configured
        
        col1, col2 = st.columns(2)
        with col1:
            if is_llm_configured():
                st.success("LLM: OK")
            else:
                st.error("LLM: Missing")
        with col2:
            if is_api_configured():
                st.success("API: OK")
            else:
                st.error("API: Missing")
                
        st.markdown("---")
        
        st.markdown("### 📚 Knowledge Base Stats")
        try:
            from modules.knowledge_base import get_kb_stats
            stats = get_kb_stats()
            st.write(f"- Strategies: **{stats['betting_strategies']}**")
            st.write(f"- Terms: **{stats['betting_terms']}**")
            st.write(f"- Team Notes: **{stats['team_analysis_notes']}**")
            st.write(f"- League Insights: **{stats['league_insights']}**")
            st.write(f"- Historical Tips: **{stats['historical_tips']}**")
            st.write(f"- FAQs: **{stats['faq']}**")
        except Exception as e:
            st.warning("Database not initialized yet.")
            
        st.markdown("---")

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            # Zamiast pustej listy, przywracamy domyślne powitanie
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Hello! I'm BetAssist AI. I can help you analyze matches, explain betting strategies, or look up team stats. What would you like to know?"
            }]
            st.rerun()
            
        st.markdown("---")
        st.caption("🤖 Powered by Gemini Flash & LangChain")
        st.caption("⚽ Live data by football-data.org")
        
        # Responsible gambling warning
        st.markdown("""
        <div style="background-color: rgba(239, 68, 68, 0.1); padding: 10px; border-radius: 5px; border-left: 4px solid #ef4444; margin-top: 20px;">
            <small style="color: #ef4444;"><b>18+ | Play Responsibly</b><br/>This tool is for informational purposes only. Betting involves risk. Do not bet more than you can afford to lose.</small>
        </div>
        """, unsafe_allow_html=True)
