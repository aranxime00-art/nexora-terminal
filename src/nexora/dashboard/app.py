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
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from nexora.dashboard.styles import apply_custom_css
from nexora.factors.indicators import calculate_momentum, calculate_rsi

st.set_page_config(page_title="NEXORA | Terminal", page_icon="⚡", layout="wide")
apply_custom_css()

# Refresco automático cada 5 segundos (simula el bot trabajando)
count = st_autorefresh(interval=5000, limit=None, key="nexora_refresh")

# --- ESTADO EN MEMORIA (Simula la base de datos) ---
if 'cash' not in st.session_state:
    st.session_state.cash = 50000.0
    st.session_state.initial_capital = 50000.0
    st.session_state.positions = {} # {"BTC/USDT": {"qty": 0.1, "buy_price": 60000}}
    st.session_state.orders = []
    st.session_state.equity_history = []
    st.session_state.bot_logs = ["Sistema iniciado. Esperando primer escaneo..."]

exchange = ccxt.mexc({'timeout': 5000})

@st.cache_data(ttl=60) 
def fetch_market_data(symbols):
    prices = {}
    signals = {}
    data_status = "LIVE DATA"
    
    for s in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(s, timeframe='1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            prices[s] = df['close'].iloc[-1]
            
            # Usamos tus indicadores reales
            mom = calculate_momentum(df['close'])['mom_1m']
            rsi = calculate_rsi(df['close'])
            
            if pd.isna(mom) or pd.isna(rsi):
                signals[s] = -999
            else:
                signals[s] = mom - (rsi / 1000)
        except Exception:
            data_status = "CONNECTION ERROR"
            
    return prices, signals, data_status

# --- LÓGICA DEL BOT (Se ejecuta en la nube) ---
tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
prices, signals, data_status = fetch_market_data(tickers)

if prices:
    # 1. Buscar el mejor activo
    top_ticker = max(signals, key=signals.get)
    
    # 2. Decidir acción
    timestamp = datetime.now().strftime('%H:%M:%S')
    current_pos = st.session_state.positions.get(top_ticker)
    
    # Si tenemos otro activo, lo vendemos
    for pos_ticker in list(st.session_state.positions.keys()):
        if pos_ticker != top_ticker:
            qty = st.session_state.positions[pos_ticker]['qty']
            sell_price = prices.get(pos_ticker, st.session_state.positions[pos_ticker]['buy_price'])
            st.session_state.cash += (qty * sell_price)
            st.session_state.orders.insert(0, {"Hora": timestamp, "Activo": pos_ticker, "Acción": "SELL", "Precio": sell_price})
            st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔄 Vendiendo {pos_ticker} para rotar a {top_ticker}.")
            del st.session_state.positions[pos_ticker]
            current_pos = None

    # Si no tenemos posición, compramos el mejor
    if not current_pos and st.session_state.cash > 10:
        buy_price = prices.get(top_ticker, 0)
        if buy_price > 0:
            qty = (st.session_state.cash * 0.95) / buy_price
            cost = qty * buy_price
            st.session_state.cash -= cost
            st.session_state.positions[top_ticker] = {"qty": qty, "buy_price": buy_price}
            st.session_state.orders.insert(0, {"Hora": timestamp, "Activo": top_ticker, "Acción": "BUY", "Precio": buy_price})
            st.session_state.bot_logs.insert(0, f"[{timestamp}] 🚀 Comprando {top_ticker} con datos reales.")

st.session_state.bot_logs = st.session_state.bot_logs[:10]

# --- CÁLCULO DE PNL Y EQUITY ---
total_positions_val = 0.0
pnl_unrealized = 0.0

for ticker, pos in st.session_state.positions.items():
    curr_price = prices.get(ticker, pos['buy_price'])
    total_positions_val += (pos['qty'] * curr_price)
    pnl_unrealized += (pos['qty'] * (curr_price - pos['buy_price']))

equity = st.session_state.cash + total_positions_val
total_return = equity - st.session_state.initial_capital

if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != equity:
    st.session_state.equity_history.append({'time': datetime.now(), 'equity': equity})

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #36C9D5 !important;'>NEXORA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 10px;'>v1.0.0 | QUANTITATIVE INTELLIGENCE</p>", unsafe_allow_html=True)
    st.divider()
    vista = st.radio("MÓDULOS", ["📈 Terminal de Trading", "🌡️ Análisis de Mercado"])
    st.divider()
    if st.button("Reiniciar Cuenta"):
        st.session_state.cash = 50000.0
        st.session_state.positions = {}
        st.session_state.orders = []
        st.session_state.equity_history = []
        st.session_state.bot_logs = ["Cuenta reiniciada."]
        st.rerun()

# --- VISTA 1: TERMINAL ---
if vista == "📈 Terminal de Trading":
    st.title("Terminal de Trading (Paper)")
    
    col_chart, col_info = st.columns([2.8, 1])
    
    with col_chart:
        status_color = "#10B981" if data_status == "LIVE DATA" else "#EF4444"
        st.markdown(f"### BTC/USDT - Velas Japonesas <span style='font-size:12px; color:{status_color};'>{data_status}</span>", unsafe_allow_html=True)
        
        # Generar gráfico usando precios reales
        try:
            ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)
            
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False))
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("No se pudieron cargar las velas reales.")
            
    with col_info:
        st.markdown("### RESUMEN")
        st.metric("EQUITY TOTAL", f"${equity:,.2f}", f"{total_return:+,.2f}")
        st.metric("EFECTIVO", f"${st.session_state.cash:,.2f}", "Disponible")
        st.metric("P&L NO REALIZADO", f"${pnl_unrealized:,.2f}", "En el mercado")
        
        st.markdown("### RIESGO")
        if len(st.session_state.equity_history) > 10:
            df_eq = pd.DataFrame(st.session_state.equity_history)
            returns = df_eq['equity'].pct_change().dropna()
            if returns.std() > 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
                roll_max = df_eq['equity'].cummax()
                drawdown = (df_eq['equity'] - roll_max) / roll_max
                max_dd = drawdown.min() * 100
                st.metric("SHARPE RATIO", f"{sharpe:.2f}", "Riesgo/Retorno")
                st.metric("MAX DRAWDOWN", f"{max_dd:.2f}%", "Peor caída")
            else:
                st.metric("SHARPE RATIO", "N/A", "Pocos datos")
        else:
            st.metric("SHARPE RATIO", "N/A", "Recopilando datos")
            st.metric("MAX DRAWDOWN", "N/A", "Recopilando datos")

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
            
    with col_orders:
        st.markdown("### LIVE BOT FEED (Nube)")
        logs_html = "<div style='background: #000; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; height: 180px; overflow-y: auto;'>"
        for log in st.session_state.bot_logs:
            color = "#10B981" if "Comprando" in log else "#EF4444" if "Vendiendo" in log else "#94A3B8"
            logs_html += f"<div style='color: {color}; margin-bottom: 4px;'>{log}</div>"
        logs_html += "</div>"
        st.markdown(logs_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("### HISTORIAL DE ÓRDENES")
    if st.session_state.orders:
        st.dataframe(pd.DataFrame(st.session_state.orders), use_container_width=True, hide_index=True)
    else:
        st.info("Esperando la primera operación del bot...")

# --- VISTA 2: MERCADO ---
elif vista == "🌡️ Análisis de Mercado":
    st.title("Análisis de Mercado")
    try:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "DOT/USDT", "LINK/USDT"]
        tickers = exchange.fetch_tickers(symbols)
        data = []
        for s in symbols:
            if s in tickers:
                data.append({"Activo": s.split('/')[0], "Cambio 24h (%)": tickers[s]['percentage']})
        
        df_market = pd.DataFrame(data)
        fig_heat = go.Figure(go.Treemap(
            labels=df_market['Activo'], parents=[""] * len(df_market), values=[1] * len(df_market),
            text=[f"{c:+.2f}%" if pd.notna(c) else "N/A" for c in df_market['Cambio 24h (%)']],
            textinfo="label+text",
            marker=dict(colors=df_market['Cambio 24h (%)'], colorscale="RdYlGn", cmid=0, line=dict(width=2, color="#0F1115"))
        ))
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    except:
        st.error("Error cargando datos de mercado desde MEXC.")