import streamlit as st


def apply_custom_css() -> None:
    """Aplica el diseño oscuro institucional de NEXORA."""
    st.markdown("""
    <style>
        .stApp {
            background-color: #111827;
            color: #F3F4F6;
        }
        
        [data-testid="stSidebar"] {
            background-color: #202C3B;
            border-right: 1px solid #374151;
        }
        
        /* Arreglar color del texto en el sidebar */
        [data-testid="stSidebar"] h1 {
            color: #36C9D5 !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: #F3F4F6 !important;
        }
        
        [data-testid="stMetric"] {
            background-color: #202C3B;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        [data-testid="stMetricValue"] {
            color: #36C9D5;
            font-family: 'Courier New', monospace;
            font-weight: 700;
        }
        
        [data-testid="stMetricLabel"] {
            color: #9CA3AF;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        h1, h2, h3 {
            color: #A855F7;
            font-family: 'Courier New', monospace;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #9CA3AF;
        }
        
        .stTabs [aria-selected="true"] {
            color: #168BCE !important;
            border-bottom-color: #168BCE !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
