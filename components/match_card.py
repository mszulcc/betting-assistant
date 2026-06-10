import streamlit as st
from datetime import datetime

def render_match_card(match: dict):
    """Renders a visually appealing match card."""
    
    # Parse date
    try:
        dt = datetime.strptime(match['date'], "%Y-%m-%d %H:%M UTC")
        date_str = dt.strftime("%b %d, %H:%M")
    except:
        date_str = match['date']

    st.markdown(f"""
    <div class="match-card">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">{match['competition']}</span>
            <span style="font-size: 0.8rem; color: #94a3b8;">{date_str}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="width: 40%; text-align: right; font-weight: bold; font-size: 1.1rem;">{match['home_team']}</div>
            <div style="width: 20%; text-align: center; color: #cbd5e1; font-weight: 800; font-size: 1.2rem;">VS</div>
            <div style="width: 40%; text-align: left; font-weight: bold; font-size: 1.1rem;">{match['away_team']}</div>
        </div>
        <div style="margin-top: 15px; text-align: center;">
            <span style="background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">STATUS: {match['status']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Analyze button
    if st.button(f"📊 Analyze {match['home_team']} vs {match['away_team']}", key=f"btn_{match['id']}"):
        st.session_state.analyze_match = match
        st.session_state.active_tab = "Chat" # Force switch to chat (requires experimental rerun or manual click instruction)
        
        # Inject prompt into chat
        prompt = f"Please provide a detailed betting analysis for the upcoming match between {match['home_team']} and {match['away_team']} in {match['competition']}."
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
