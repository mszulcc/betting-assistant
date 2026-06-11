import streamlit as st


def render_navbar():
    """Renders the top navigation bar, disguised as tabs with global layout locks."""
    st.markdown("""
            <style>
            /* --- GLOBALNA BLOKADA EKRANU --- */
            [data-testid="stAppViewContainer"] > .main {
                overflow: hidden !important;
                height: 100vh !important; /* <--- TO ZABIJA SKAKANIE: Wymusza 100% wysokości ekranu */
            }

            html, body, [data-testid="stAppViewContainer"] {
                scroll-behavior: auto !important; 
            }

            /* Odblokowanie miejsca dla paska czatu na dole */
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 5rem !important; 
            }
            /* Zamiast chować cały header, chowamy tylko zbędne menu po prawej stronie */
            #MainMenu {visibility: hidden;}
            .stAppDeployButton {display: none;}
            footer {visibility: hidden;}
            
            /* Robimy header przezroczystym, żeby nie zasłaniał naszej aplikacji, 
               ale zostawiamy go widocznym dla przycisku sidebara! */
            header {background-color: transparent !important;}

            /* --- MAGIA CSS: ZAKŁADKI --- */
            div[role="radiogroup"] label > div:first-of-type { display: none !important; }

            div[role="radiogroup"] {
                display: flex;
                flex-direction: row;
                gap: 2rem;
                border-bottom: 1px solid #e0e0e0; 
                padding-bottom: 0 !important;
            }

            div[role="radiogroup"] label {
                cursor: pointer;
                padding-bottom: 0.5rem;
                margin-bottom: -1px; 
                border-bottom: 3px solid transparent; 
                transition: all 0.2s ease-in-out;
            }

            div[role="radiogroup"] label:has(input:checked) {
                border-bottom: 3px solid #FF4B4B !important; 
            }

            div[role="radiogroup"] label:has(input:checked) p {
                font-weight: 600 !important;
                color: #FF4B4B !important;
            }

            div[role="radiogroup"] p {
                margin: 0;
                font-size: 1.1rem;
            }
            </style>
        """, unsafe_allow_html=True)

    # ... (Twój zaawansowany CSS bez zmian)

    options = ["💬 Chat", "⚽ Upcoming Matches", "📊 Standings", "📚 Knowledge Base"]

    # 1. Poprawna inicjalizacja: robimy to TYLKO RAZ na samym początku uruchomienia aplikacji.
    # Jeśli klucz już istnieje w sesji (bo np. przycisk Analyze go zmienił), to go NIE NADPISUJEMY.
    if "active_page" not in st.session_state:
        st.session_state.active_page = "💬 Chat"

    # 2. Powiązanie z radiogroup poprzez parametr 'key'.
    # Usunęliśmy przypisywanie zmiennej 'selected' z powrotem do st.radio.
    # Streamlit sam zaktualizuje st.session_state.active_page po kliknięciu.
    st.radio(
        "Menu",
        options,
        horizontal=True,
        label_visibility="collapsed",
        key="active_page"  # To jest kluczowe!
    )

    # Zwracamy aktualną wartość prosto z sesji
    return st.session_state.active_page