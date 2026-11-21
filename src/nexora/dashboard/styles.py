import streamlit as st

def apply_custom_css() -> None:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Roboto+Mono:wght@400;500&display=swap');

        /* Fondo Global (Charcoal Oscuro) */
        .stApp {
            background-color: #0F1115;
            color: #E2E8F0;
            font-family: 'Inter', sans-serif;
        }

        /* Ocultar el Sidebar por completo */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Dar más espacio al contenido principal */
        .block-container {
            padding-top: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 95% !important;
        }

        /* Ocultar menús de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Títulos */
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        h1 { font-size: 1.5rem !important; margin-bottom: 0.5rem !important; }
        h2 { font-size: 1.2rem !important; margin-top: 1rem !important; margin-bottom: 0.5rem !important; }
        h3 { font-size: 1rem !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; }

        /* Navegación Superior (st.radio horizontal) */
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            flex-direction: row !important;
            justify-content: center !important;
            gap: 20px !important;
        }
        
        div[data-testid="stRadio"] label {
            background-color: transparent !important;
            padding: 8px 16px !important;
            border-radius: 6px !important;
            border: 1px solid transparent !important;
        }
        
        div[data-testid="stRadio"] label:hover {
            background-color: #1A1D23 !important;
        }
        
        div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
            display: none !important; /* Ocultar el circulito del radio button */
        }
        
        div[data-testid="stRadio"] label p {
            color: #94A3B8 !important;
            font-family: 'Inter', sans-serif;
            font-size: 14px !important;
            font-weight: 500 !important;
        }
        
        div[data-testid="stRadio"] label[aria-checked="true"] {
            background-color: #1A1D23 !important;
            border: 1px solid #3B82F6 !important;
        }
        
        div[data-testid="stRadio"] label[aria-checked="true"] p {
            color: #FFFFFF !important;
        }

        /* Tarjetas de Métricas (Laterales) */
        [data-testid="stMetric"] {
            background-color: #1A1D23 !important;
            border: 1px solid #2A2E35;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
            box-shadow: none;
        }
        
        [data-testid="stMetricValue"] > div {
            color: #E2E8F0 !important;
            font-family: 'Roboto Mono', monospace;
            font-weight: 500;
            font-size: 20px !important;
        }
        [data-testid="stMetricLabel"] > div {
            color: #94A3B8 !important;
            font-size: 11px !important;
            font-weight: 500;
            text-transform: uppercase;
        }

        /* Botones */
        .stButton>button {
            background-color: #2A2E35;
            color: #E2E8F0;
            border: 1px solid #3F444D;
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #3B82F6;
            color: #FFFFFF;
            border-color: #3B82F6;
        }

        /* Tablas */
        .nexora-table {
            width: 100%; 
            border-collapse: collapse; 
            background-color: #1A1D23; 
            border: 1px solid #2A2E35; 
            border-radius: 6px; 
            overflow: hidden;
            font-family: 'Roboto Mono', monospace; 
            font-size: 12px;
        }
        .nexora-table th {
            background-color: #0F1115; 
            color: #94A3B8; 
            text-align: left;
            padding: 10px 12px; 
            border-bottom: 1px solid #2A2E35; 
            font-family: 'Inter', sans-serif; 
            font-size: 11px;
            text-transform: uppercase;
        }
        .nexora-table td { 
            padding: 10px 12px; 
            border-bottom: 1px solid #2A2E35; 
            color: #E2E8F0; 
        }
        .nexora-table tr:hover { 
            background-color: #232730; 
        }
        
        /* Logs del Bot */
        .bot-logs {
            background-color: #000000; 
            border: 1px solid #2A2E35; 
            border-radius: 4px;
            padding: 12px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 11px;
            height: 250px; 
            overflow-y: auto; 
            color: #94A3B8; 
        }
        
        /* Header Top Bar */
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 10px;
            border-bottom: 1px solid #2A2E35;
            margin-bottom: 20px;
        }
        .top-bar-left { font-size: 12px; color: #94A3B8; font-family: 'Roboto Mono', monospace; }
        .top-bar-right { font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)