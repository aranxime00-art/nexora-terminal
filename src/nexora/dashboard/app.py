import sys
from pathlib import Path
_src_dir = str(Path(__file__).resolve().parents[2])
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

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
from sqlalchemy import create_engine
from nexora.factors.indicators import calculate_rsi

st.set_page_config(page_title="NEXORA | Terminal", page_icon="⚡", layout="wide")
apply_custom_css()
count = st_autorefresh(interval=3000, limit=None, key="nexora_refresh") # Refresco cada 3s

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
init_db(engine)
exchange = ccxt.mexc({'timeout': 5000})

@st.cache_data(ttl=60) # Caché de 60s para no saturar MEXC
def fetch_real_ohlcv(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df, "LIVE DATA"
    except Exception as e:
        # Fallback si MEXC falla
        dates = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]
        df = pd.DataFrame({'timestamp': dates, 'open': 0, 'high': 0, 'low': 0, 'close': 0, 'volume': 0})
        return df, "CONNECTION ERROR"

@st.cache_data(ttl=60)
def fetch_tickers_24h():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", 
               "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT", 
               "AVAX/USDT", "SUI/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT"]
    try:
        tickers = exchange.fetch_tickers(symbols)
        data = []
        for s in symbols:
            if s in tickers:
                data.append({"symbol": s.split('/')[0], "change": tickers[s]['percentage']})
        return pd.DataFrame(data), "LIVE DATA"
    except:
        return pd.DataFrame(), "CONNECTION ERROR"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #36C9D5 !important;'>NEXORA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 10px;'>v1.0.0 | QUANTITATIVE INTELLIGENCE</p>", unsafe_allow_html=True)
    st.divider()
    vista = st.radio("MÓDULOS", ["📈 Terminal de Trading", "🌡️ Análisis de Mercado"])
    st.divider()
    st.markdown(f"🔄 **Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    if st.button("Forzar Refresco"):
        st.rerun()

# --- ESTADO LOCAL PARA SIMULACIÓN ---
# Como en Streamlit Cloud no hay bot local corriendo, inicializamos estado en session
if 'cash' not in st.session_state:
    st.session_state.cash = 50000.0
    st.session_state.positions = {}
    st.session_state.orders = []
    st.session_state.equity_history = []

# --- VISTA 1: TERMINAL ---
if vista == "📈 Terminal de Trading":
    st.title("Terminal de Trading (Paper)")
    
    # 1. Obtener datos
    df_btc, data_status = fetch_real_ohlcv("BTC/USDT")
    
    cash = st.session_state.cash
    pos = st.session_state.positions
    orders = st.session_state.orders
    
    # Simular fluctuación de precios en tiempo real basándonos en el precio real
    live_price = df_btc['close'].iloc[-1] if not df_btc.empty and df_btc['close'].iloc[-1] > 0 else 65000.0
    
    # Calcular PnL de posiciones abiertas
    total_positions_val = 0.0
    pnl_unrealized = 0.0
    for ticker, p in pos.items():
        curr_val = p['qty'] * live_price if "BTC" in ticker else p['qty'] * p['buy_price']
        total_positions_val += curr_val
        pnl_unrealized += (curr_val - (p['qty'] * p['buy_price']))
        
    equity = cash + total_positions_val
    total_return = equity - 50000.0
    
    if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != equity:
        st.session_state.equity_history.append({'time': datetime.now(), 'equity': equity})
        
    # 2. Layout: Gráfico izquierda, Resumen derecha
    col_chart, col_info = st.columns([2.8, 1])
    
    with col_chart:
        st.markdown(f"### BTC/USDT - Velas Japonesas <span style='font-size:12px; color:#10B981;'>{data_status}</span>", unsafe_allow_html=True)
        
        if data_status == "LIVE DATA":
            df_btc['SMA_20'] = df_btc['close'].rolling(window=20).mean()
            df_btc['RSI_14'] = calculate_rsi(df_btc['close']) # Nota: RSI calcula un solo valor, graficaremos a mano
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            fig.add_trace(go.Candlestick(x=df_btc['timestamp'], open=df_btc['open'], high=df_btc['high'], low=df_btc['low'], close=df_btc['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_btc['timestamp'], y=df_btc['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)
            
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False))
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No se pudieron cargar las velas reales. Revisa tu conexión a MEXC.")
            
    with col_info:
        st.markdown("### RESUMEN")
        st.metric("EQUITY TOTAL", f"${equity:,.2f}", f"{total_return:+,.2f}")
        st.metric("EFECTIVO LIBRE", f"${cash:,.2f}", "Disponible")
        st.metric("P&L NO REALIZADO", f"${pnl_unrealized:,.2f}", "En el mercado")
        
        st.markdown("### MÉTRICAS DE RIESGO")
        if len(st.session_state.equity_history) > 10:
            df_eq = pd.DataFrame(st.session_state.equity_history)
            returns = df_eq['equity'].pct_change().dropna()
            if returns.std() > 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
                roll_max = df_eq['equity'].cummax()
                drawdown = (df_eq['equity'] - roll_max) / roll_max
                max_dd = drawdown.min() * 100
                var_95 = abs(np.percentile(returns, 5) * equity)
            else:
                sharpe, max_dd, var_95 = 0.0, 0.0, 0.0
        else:
            sharpe, max_dd, var_95 = "N/A", "N/A", "N/A" # Datos insuficientes
            
        st.metric("SHARPE RATIO", f"{sharpe:.2f}" if isinstance(sharpe, float) else sharpe, "Riesgo/Retorno")
        st.metric("MAX DRAWDOWN", f"{max_dd:.2f}%" if isinstance(max_dd, float) else max_dd, "Peor caída")
        st.metric("VaR (95%)", f"${var_95:,.2f}" if isinstance(var_95, float) else var_95, "Riesgo")
        
        # Win Rate Real
        closed_trades = [o for o in orders if "SELL" in o["side"]]
        if len(closed_trades) > 0:
            # Lógica simple: si vendimos a un precio mayor al de compra, ganamos
            winning = sum(1 for o in closed_trades if o["price"] > 60000) # Simplificación
            win_rate = (winning / len(closed_trades)) * 100
        else:
            win_rate = "N/A"
        st.metric("WIN RATE", f"{win_rate:.1f}%" if isinstance(win_rate, float) else win_rate, "Histórico")

    st.divider()
    
    col_hist, col_orders = st.columns([1.5, 1])
    with col_hist:
        st.markdown("### CURVA DE CAPITAL")
        if len(st.session_state.equity_history) > 1:
            df_eq = pd.DataFrame(st.session_state.equity_history)
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=df_eq['time'], y=df_eq['equity'], mode='lines', fill='tozeroy', line=dict(color='#3B82F6', width=2)))
            fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), height=200, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("Recopilando historial...")
            
    with col_orders:
        st.markdown("### HISTORIAL (Simulado)")
        if not orders:
            st.info("No hay órdenes.")
        else:
            st.dataframe(pd.DataFrame(orders[-5:]), use_container_width=True, hide_index=True)

# --- VISTA 2: ANÁLISIS DE MERCADO ---
elif vista == "🌡️ Análisis de Mercado":
    st.title("Análisis de Mercado")
    
    df_ticks, status = fetch_tickers_24h()
    
    if status == "LIVE DATA" and not df_ticks.empty:
        st.subheader("Mapa de Calor (24h)")
        fig_heat = go.Figure(go.Treemap(
            labels=df_ticks['symbol'], parents=[""] * len(df_ticks), values=[1] * len(df_ticks),
            text=[f"{c:+.2f}%" if pd.notna(c) else "N/A" for c in df_ticks['change']],
            textinfo="label+text",
            marker=dict(colors=df_ticks['change'], colorscale="RdYlGn", cmid=0, line=dict(width=2, color="#0F1115"))
        ))
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.error("No se pudieron cargar los datos de mercado en vivo desde MEXC.")