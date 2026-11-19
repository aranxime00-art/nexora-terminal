import streamlit as st

def apply_custom_css() -> None:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
        
        .stApp {
            background-color: #0B1120;
            background-image: radial-gradient(circle at 50% 0%, rgba(22, 139, 206, 0.15) 0%, transparent 50%);
            color: #FFFFFF;
            font-family: 'Rajdhani', sans-serif;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
            text-shadow: 0 0 12px rgba(54, 201, 213, 0.6) !important;
            font-family: 'Rajdhani', sans-serif;
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.95) !important;
            border-right: 1px solid #36C9D5;
        }
        
        .stButton>button {
            background-color: #1E293B;
            color: #FFFFFF;
            border: 1px solid #36C9D5;
        }
        .stButton>button:hover { background-color: #36C9D5; color: #000000; }

        .stSelectbox label, .stNumberInput label { color: #FFFFFF !important; font-weight: bold; }

        [data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.8) !important;
            border-left: 4px solid #36C9D5 !important;
            border-radius: 8px;
            padding: 15px;
        }
        [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] p { color: #FFFFFF !important; }
        [data-testid="stMetricValue"] > div {
            color: #36C9D5 !important;
            font-family: 'Share Tech Mono', monospace;
            text-shadow: 0 0 10px rgba(54, 201, 213, 0.8);
        }

        .nexora-table {
            width: 100%; border-collapse: collapse; background: rgba(30, 41, 59, 0.8);
            border: 1px solid #36C9D5; font-family: 'Share Tech Mono', monospace; font-size: 15px;
        }
        .nexora-table th {
            background: rgba(22, 139, 206, 0.4); color: #FFFFFF; text-align: left;
            padding: 12px; border-bottom: 2px solid #36C9D5;
        }
        .nexora-table td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #FFFFFF; }
        .nexora-table tr:hover { background: rgba(54, 201, 213, 0.2); }
        
        /* NO ocultamos el header para que puedas abrir/cerrar el menú */
        footer {visibility: hidden;} 
    </style>
    """, unsafe_allow_html=True)