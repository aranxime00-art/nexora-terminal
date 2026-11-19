import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from nexora.dashboard.styles import apply_custom_css
from sqlalchemy.orm import Session
from nexora.data.database import get_engine, Account, Position, TradeOrder, MarketPrice, init_db

st.set_page_config(page_title="NEXORA | Terminal", page_icon="📈", layout="wide")
apply_custom_css()

# REFRESCO CADA 1 SEGUNDO
count = st_autorefresh(interval=1000, limit=None, key="nexora_refresh")

engine = get_engine()
init_db(engine)

# Inicializar el historial de la curva de capital en memoria
if 'equity_history' not in st.session_state:
    st.session_state.equity_history = []

@st.cache_data(ttl=5) 
def get_real_candles(symbol: str):
    try:
        exchange = ccxt.mexc({'timeout': 2000})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=60)
        if ohlcv:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df, True
    except Exception:
        pass
        
    # Respaldo
    dates = [datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)]
    base = 65000 if "BTC" in symbol else 3500 if "ETH" in symbol else 150
    data = []
    current = base * 0.98
    for i in range(60):
        open_p = current
        close_p = open_p * (1 + np.random.randn() * 0.002)
        high_p = max(open_p, close_p) * 1.001
        low_p = min(open_p, close_p) * 0.999
        data.append({'timestamp': dates[i], 'open': open_p, 'high': high_p, 'low': low_p, 'close': close_p})
        current = close_p
    return pd.DataFrame(data), False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #36C9D5 !important;'>NEXORA</h1>", unsafe_allow_html=True)
    st.divider()
    st.subheader("Gestión de Cuenta")
    capital_inicial = st.number_input("Capital Inicial (USD)", min_value=100.0, value=50000.0, step=1000.0)
    
    if st.button("Reiniciar Cuenta"):
        with Session(engine) as session:
            session.query(Account).delete()
            session.query(Position).delete()
            session.query(TradeOrder).delete()
            session.add(Account(cash=capital_inicial, initial_capital=capital_inicial))
            session.commit()
        st.session_state.equity_history = [] # Limpiar curva al reiniciar
        st.success(f"Cuenta reiniciada con ${capital_inicial:,.2f}.")
        st.rerun()

    if st.button("Retirar TODO el Efectivo"):
        with Session(engine) as session:
            acc_db = session.query(Account).first()
            if acc_db and acc_db.cash > 0:
                retiro = acc_db.cash
                acc_db.cash = 0.0
                session.add(TradeOrder(ticker="RETIRO TOTAL", side="WITHDRAW", quantity=retiro, price=1.0, commission=0.0, slippage=0.0))
                session.commit()
                st.success("Retiro total exitoso.")
            else:
                st.warning("No hay efectivo para retirar.")
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("Terminal de Trading (Simulador MEXC)")

with Session(engine) as session:
    acc = session.query(Account).first()
    if acc is None:
        acc = Account(cash=50000.0, initial_capital=50000.0)
        session.add(acc)
        session.commit()
    
    pos = session.query(Position).all()
    orders = session.query(TradeOrder).order_by(TradeOrder.timestamp.desc()).limit(10).all()
    
    db_prices = session.query(MarketPrice).all()
    prices = {mp.ticker: mp.price for mp in db_prices}
    
    cash = acc.cash
    initial_cap = acc.initial_capital

# Calcular P&L
total_positions_value = 0.0
pnl_total = 0.0
for p in pos:
    curr_price = prices.get(p.ticker, p.average_price)
    total_positions_value += p.quantity * curr_price
    pnl_total += (curr_price - p.average_price) * p.quantity

total_equity = cash + total_positions_value
total_return = total_equity - initial_cap

# GUARDAR EN EL HISTORIAL PARA LA CURVA DE CAPITAL
if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != total_equity:
    st.session_state.equity_history.append({'time': datetime.now(), 'equity': total_equity})
    # Mantener solo los últimos 100 registros para no saturar la memoria
    if len(st.session_state.equity_history) > 100:
        st.session_state.equity_history.pop(0)

# Tarjetas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Patrimonio Total", "${:,.2f}".format(total_equity), "{:+,.2f}".format(total_return))
col2.metric("Efectivo Libre", "${:,.2f}".format(cash), "Disponible")
col3.metric("Valor en Activos", "${:,.2f}".format(total_positions_value), "En el mercado")
col4.metric("P&L No Realizado", "${:,.2f}".format(pnl_total), "Ganancia/Pérdida")

st.divider()

col_chart, col_data = st.columns([2.5, 1])

with col_chart:
    selected_asset = st.selectbox("Seleccionar Activo para Gráfico", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"])
    
    df, is_live = get_real_candles(selected_asset)
    
    if not is_live:
        st.warning("⚠️ MEXC no responde. Mostrando gráfico de respaldo.")

    # Calcular Indicadores
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))

    # Crear Subplots (Precio arriba, RSI abajo)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.75, 0.25],
                        subplot_titles=(f"{selected_asset} - Velas Japonesas", "RSI (14)"))

    # Panel 1: Velas
    fig.add_trace(go.Candlestick(
        x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='#10B981', decreasing_line_color='#EF4444', name="Precio"
    ), row=1, col=1)
    
    # Panel 1: SMA 20
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['SMA_20'], mode='lines', 
        line=dict(color='#F59E0B', width=2), name="SMA 20"
    ), row=1, col=1)

    # Panel 1: Línea de Precio Actual
    current_price = prices.get(selected_asset, df['close'].iloc[-1])
    fig.add_trace(go.Scatter(
        x=[df['timestamp'].iloc[0], df['timestamp'].iloc[-1]],
        y=[current_price, current_price],
        mode='lines', line=dict(color='#36C9D5', width=1, dash='dot'), name="Live Price"
    ), row=1, col=1)

    # Panel 2: RSI
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['RSI_14'], mode='lines', 
        line=dict(color='#A855F7', width=2), name="RSI"
    ), row=2, col=1)
    
    # Zonas de sobrecompra/sobreventa en RSI
    fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#10B981", row=2, col=1)

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF', size=11),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False), tickfont=dict(color='#FFFFFF')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Precio (USDT)", title_font=dict(color='#36C9D5'), tickfont=dict(color='#FFFFFF')),
        yaxis2=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="RSI", title_font=dict(color='#A855F7'), range=[0, 100], tickfont=dict(color='#FFFFFF')),
        margin=dict(l=0, r=0, t=30, b=0), height=550,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("Posiciones Abiertas")
    if not pos:
        st.markdown("<div style='background-color: #1E293B; padding: 15px; border-radius: 5px; color: #FFFFFF;'>Sin posiciones. Esperando que el bot ejecute la primera compra.</div>", unsafe_allow_html=True)
    else:
        html = "<table class='nexora-table'><tr><th>Activo</th><th>Cant</th><th>Compra</th><th>Actual</th><th>P&L</th></tr>"
        for p in pos:
            curr_price = prices.get(p.ticker, p.average_price)
            pnl = (curr_price - p.average_price) * p.quantity
            color = "#10B981" if pnl >= 0 else "#EF4444"
            html += f"<tr><td>{p.ticker.split('/')[0]}</td><td>{p.quantity:.4f}</td><td>${p.average_price:,.2f}</td><td>${curr_price:,.2f}</td><td style='color:{color}; font-weight:bold;'>{pnl:+,.2f}</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

st.divider()

# --- CURVA DE CAPITAL E HISTORIAL ---
col_equity, col_history = st.columns([1.5, 1])

with col_equity:
    st.subheader("Curva de Capital (Equity Curve)")
    if len(st.session_state.equity_history) > 1:
        df_equity = pd.DataFrame(st.session_state.equity_history)
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=df_equity['time'], y=df_equity['equity'],
            mode='lines', fill='tozeroy',
            line=dict(color='#36C9D5', width=2),
            fillcolor='rgba(54, 201, 213, 0.1)'
        ))
        fig_eq.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF'),
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            margin=dict(l=0, r=0, t=10, b=0), height=250
        )
        st.plotly_chart(fig_eq, use_container_width=True)
    else:
        st.info("Recopilando datos para la curva de capital...")

with col_history:
    st.subheader("Historial de Órdenes")
    if not orders:
        st.markdown("<div style='background-color: #1E293B; padding: 15px; border-radius: 5px; color: #FFFFFF;'>Aún no hay registros.</div>", unsafe_allow_html=True)
    else:
        html_orders = "<table class='nexora-table'><tr><th>Hora</th><th>Activo</th><th>Acción</th><th>Precio</th></tr>"
        for o in orders[:5]: # Mostrar solo las últimas 5 para no hacerla tan larga
            color = "#10B981" if o.side in ["BUY", "WITHDRAW"] else "#EF4444"
            html_orders += f"<tr><td>{o.timestamp.strftime('%H:%M:%S')}</td><td>{o.ticker.split('/')[0]}</td><td style='color:{color}; font-weight:bold;'>{o.side}</td><td>${o.price:,.2f}</td></tr>"
        html_orders += "</table>"
        st.markdown(html_orders, unsafe_allow_html=True)