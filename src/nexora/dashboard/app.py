import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from nexora.dashboard.styles import apply_custom_css

st.set_page_config(page_title="NEXORA", page_icon="📈", layout="wide")
apply_custom_css()

with st.sidebar:
    st.title("NEXORA")
    st.markdown("*QUANTITATIVE INTELLIGENCE*")
    st.divider()

    opcion = st.radio(
        "Navegación",
        ["Inicio", "Mercado", "Ranking NEXORA", "Portafolio", "Centro de Inteligencia"]
    )
    st.divider()
    st.caption("Estado del Motor: 🟢 Online")
    st.caption("Modo: PAPER TRADING")

if opcion == "Inicio":
    st.title("Panel de Control")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patrimonio Total", "$10,450.20", "+4.5%")
    col2.metric("Efectivo", "$2,000.00", "-")
    col3.metric("Drawdown Actual", "-1.2%", "Max: -5.4%")
    col4.metric("Régimen", "Expansión", "SPY > SMA200")

    st.divider()

    st.subheader("Evolución del Patrimonio")
    fechas = pd.date_range(start="2024-01-01", periods=100, freq="B")

    # Generar una curva de equity más realista (Random Walk con sesgo positivo)
    np.random.seed(42)
    retornos = np.random.normal(0.001, 0.01, 100)
    equity = 10000 * np.exp(np.cumsum(retornos))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fechas, y=equity,
        mode='lines',
        line=dict(color='#168BCE', width=2),
        fill='tozeroy',
        fillcolor='rgba(22, 139, 206, 0.1)'
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#374151'),
        margin=dict(l=0, r=0, t=10, b=0),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

elif opcion == "Ranking NEXORA":
    st.title("Ranking Cuantitativo")
    st.markdown("Clasificación de activos según el *Composite Score*.")

    data = {
        "Activo": ["SPY", "QQQ", "GLD", "TLT", "VNQ"],
        "Score": [88.5, 76.2, 65.0, 45.3, 32.1],
        "Momentum": [0.15, 0.12, 0.05, -0.02, -0.05],
        "RSI (14)": [65, 58, 52, 40, 35],
        "Volatilidad": ["12%", "15%", "10%", "18%", "22%"]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.title(f"Módulo: {opcion}")
    st.info("Módulo en construcción.")
