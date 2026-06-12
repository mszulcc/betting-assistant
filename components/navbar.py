import streamlit as st


def render_navbar():
    """Renders the top navigation bar with fake tabs and dynamic full-height locked layout."""
    st.markdown("""
        <style>
        /* 1. CAŁKOWITA BLOKADA PRZEWIJANIA STRONY GŁÓWNEJ */
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow: hidden !important;
            height: 100vh !important;
            margin: 0;
            padding: 0;
        }

        ::-webkit-scrollbar {
            width: 0px !important;
            background: transparent !important;
        }

        /* 2. ZABICIE "SLAJDÓW" (LAYOUT SHIFT) */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 6rem !important; /* Sztywna rezerwacja miejsca na input czatu */
            max-height: 100vh !important;
            overflow: hidden !important; 
        }

        /* 3. DYNAMICZNE WYPEŁNIENIE EKRANU (NOWOŚĆ) */
        /* Celujemy we wszystkie kontenery, którym Python nadał sztywną wysokość i zmuszamy je do rozciągnięcia */
        [data-testid="stScrollableContainer"],
        [data-testid="stVerticalBlockBorderWrapper"],
        div[style*="height: 600px"] {
            height: calc(100vh - 10.5rem) !important; /* Idealne dopasowanie: 100% ekranu minus marginesy */
            max-height: none !important;
        }

        /* Ukrywanie menu Streamlita */
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {display: none;}
        footer {visibility: hidden;}
        header {background-color: transparent !important;}

        /* --- MAGIA CSS: ZAKŁADKI --- */
        div[role="radiogroup"] {
            display: flex;
            flex-direction: row;
            align-items: flex-end; /* Wymusza dociśnięcie wszystkich zakładek do dolnej krawędzi */
            gap: 2rem;
            border-bottom: 2px solid #e0e0e0; /* Solidna szara linia tła */
            padding-bottom: 0 !important;
            margin-bottom: 1.5rem; /* Margines oddzielający navbar od reszty strony */
        }

        /* Ukrycie kółek radio */
        div[role="radiogroup"] label > div:first-of-type { 
            display: none !important; 
        }

        /* Główny kontener klikalny */
        div[role="radiogroup"] label {
            cursor: pointer;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 0.2rem 0.5rem 0.2rem !important; /* Równy odstęp tekstu od linii */
            margin: 0 !important;
            margin-bottom: -2px !important; /* Nachodzi idealnie na szarą linię (musi być równe border-bottom z góry!) */
            border-bottom: 3px solid transparent !important; 
            transition: border-color 0.2s ease-in-out;
        }

        /* Brutalne wyzerowanie ukrytych marginesów Streamlita wokół liter */
        div[role="radiogroup"] label div, 
        div[role="radiogroup"] label p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
        }

        /* Styl samego tekstu */
        div[role="radiogroup"] p {
            font-size: 1.1rem;
            transition: color 0.2s ease-in-out;
        }

        /* Zaznaczona zakładka (Czerwona linia i pogrubienie) */
        div[role="radiogroup"] label:has(input:checked) {
            border-bottom: 3px solid #FF4B4B !important; 
        }

        div[role="radiogroup"] label:has(input:checked) p {
            font-weight: 600 !important;
            color: #FF4B4B !important;
        }
        </style>
    """, unsafe_allow_html=True)

    options = ["💬 Chat", "⚽ Upcoming Matches", "📊 Standings", "📚 Knowledge Base"]

    if "active_page" not in st.session_state:
        st.session_state.active_page = "💬 Chat"

    st.radio("Menu", options, horizontal=True, label_visibility="collapsed", key="active_page")

    return st.session_state.active_page