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

        /* Ocultar elementos básicos de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Sidebar (Graphite) */
        [data-testid="stSidebar"] {
            background-color: #16191D !important;
            border-right: 1px solid #2A2E35;
        }

        /* Títulos Principales */
        h1, h2, h3 {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        
        h1 { font-size: 1.8rem !important; margin-bottom: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; margin-top: 1.5rem !important; margin-bottom: 1rem !important; border-bottom: 1px solid #2A2E35; padding-bottom: 0.5rem; }
        h3 { font-size: 1.1rem !important; color: #94A3B8 !important; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem !important; }

        /* Tarjetas de Métricas (Estilo Institucional, sin Glassmorphism) */
        [data-testid="stMetric"] {
            background-color: #1A1D23 !important;
            border: 1px solid #2A2E35;
            border-radius: 6px;
            padding: 16px;
            box-shadow: none;
        }
        
        /* Valores de las Métricas */
        [data-testid="stMetricValue"] > div {
            color: #E2E8F0 !important;
            font-family: 'Roboto Mono', monospace;
            font-weight: 500;
            font-size: 24px !important;
        }
        [data-testid="stMetricLabel"] > div {
            color: #94A3B8 !important;
            font-family: 'Inter', sans-serif;
            font-size: 12px !important;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Delta (Positivo/Negativo) */
        [data-testid="stMetricDelta"] > div {
            font-family: 'Roboto Mono', monospace;
            font-size: 14px !important;
            font-weight: 500;
        }

        /* Botones (Azul Institucional) */
        .stButton>button {
            background-color: #2A2E35;
            color: #E2E8F0;
            border: 1px solid #3F444D;
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #3B82F6;
            color: #FFFFFF;
            border-color: #3B82F6;
        }
        
        /* Botón Primario (Reiniciar) */
        .stButton>button[kind="primary"] {
            background-color: #3B82F6;
            color: white;
            border: none;
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #2563EB;
        }

        /* Radio Buttons del Sidebar */
        [data-testid="stRadio"] label p {
            color: #94A3B8 !important;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
        }
        [data-testid="stRadio"] [aria-checked="true"] ~ div p {
            color: #FFFFFF !important;
        }

        /* Inputs y Selectores */
        .stSelectbox > div > div, .stNumberInput > div > div {
            background-color: #1A1D23 !important;
            border: 1px solid #2A2E35 !important;
            color: #E2E8F0 !important;
            border-radius: 4px;
        }

        /* Tablas (Estilo Institucional) */
        .nexora-table {
            width: 100%; 
            border-collapse: collapse; 
            background-color: #1A1D23; 
            border: 1px solid #2A2E35; 
            border-radius: 6px; 
            overflow: hidden;
            font-family: 'Roboto Mono', monospace; 
            font-size: 13px;
        }
        .nexora-table th {
            background-color: #0F1115; 
            color: #94A3B8; 
            text-align: left;
            padding: 12px 16px; 
            border-bottom: 1px solid #2A2E35; 
            font-family: 'Inter', sans-serif; 
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .nexora-table td { 
            padding: 12px 16px; 
            border-bottom: 1px solid #2A2E35; 
            color: #E2E8F0; 
        }
        .nexora-table tr:hover { 
            background-color: #232730; 
        }
        
        /* Logs del Bot (Estilo Terminal) */
        .bot-logs {
            background-color: #000000; 
            border: 1px solid #2A2E35; 
            border-radius: 4px;
            padding: 16px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 12px;
            height: 450px; 
            overflow-y: auto; 
            color: #94A3B8; 
        }
    </style>
    """, unsafe_allow_html=True)