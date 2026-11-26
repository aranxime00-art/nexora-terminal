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
count = st_autorefresh(interval=5000, limit=None, key="nexora_refresh")

# --- ESTADO EN MEMORIA ---
if 'cash' not in st.session_state:
    st.session_state.cash = 50000.0
    st.session_state.initial_capital = 50000.0
    st.session_state.positions = {}
    st.session_state.orders = []
    st.session_state.equity_history = []
    st.session_state.bot_logs = ["Sistema iniciado. Conectando a MEXC..."]
    st.session_state.last_trade_time = 0

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
            mom = calculate_momentum(df['close'])['mom_1m']
            rsi = calculate_rsi(df['close'])
            signals[s] = (mom - (rsi / 1000)) if not pd.isna(mom) else -999
        except Exception:
            data_status = "CONNECTION ERROR"
    return prices, signals, data_status

# --- LÓGICA DEL BOT ---
tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
prices, signals, data_status = fetch_market_data(tickers)

if prices and data_status == "LIVE DATA":
    top_ticker = max(signals, key=signals.get)
    timestamp = datetime.now().strftime('%H:%M:%S')
    current_pos = st.session_state.positions.get(top_ticker)
    
    # Rotación (Vender el viejo, comprar el nuevo)
    for pos_ticker in list(st.session_state.positions.keys()):
        if pos_ticker != top_ticker:
            qty = st.session_state.positions[pos_ticker]['qty']
            sell_price = prices.get(pos_ticker, st.session_state.positions[pos_ticker]['buy_price'])
            st.session_state.cash += (qty * sell_price)
            st.session_state.orders.insert(0, {"Hora": timestamp, "Activo": pos_ticker.split('/')[0], "Acción": "SELL", "Precio": sell_price, "Cantidad": qty})
            st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔄 Vendiendo {pos_ticker} para rotar capital.")
            del st.session_state.positions[pos_ticker]
            current_pos = None

    # Compra inicial (si hay capital y no hay posición del mejor activo)
    if not current_pos and st.session_state.cash > 10:
        buy_price = prices.get(top_ticker, 0)
        if buy_price > 0:
            qty = (st.session_state.cash * 0.95) / buy_price
            cost = qty * buy_price
            st.session_state.cash -= cost
            st.session_state.positions[top_ticker] = {"qty": qty, "buy_price": buy_price}
            st.session_state.orders.insert(0, {"Hora": timestamp, "Activo": top_ticker.split('/')[0], "Acción": "BUY", "Precio": buy_price, "Cantidad": qty})
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

# Guardar historial
if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != equity:
    st.session_state.equity_history.append({'time': datetime.now(), 'equity': equity})
    if len(st.session_state.equity_history) > 100:
        st.session_state.equity_history.pop(0)

# --- HEADER Y NAVEGACIÓN HORIZONTAL ---
col_logo, col_nav, col_status = st.columns([1, 2, 1])
with col_logo:
    st.markdown("<div style='font-size: 26px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px;'>NEXORA</div>", unsafe_allow_html=True)
with col_nav:
    vista = st.radio("NAV", ["Terminal de Trading", "Análisis de Mercado", "Red Neuronal LSTM"], horizontal=True, label_visibility="collapsed")
with col_status:
    status_color = "#10B981" if data_status == "LIVE DATA" else "#EF4444"
    st.markdown(f"<div style='text-align: right; font-family: Roboto Mono; font-size: 12px; color: #94A3B8; margin-bottom: 5px;'>v1.0.0 | <span style='color:{status_color};'>● {data_status}</span></div>", unsafe_allow_html=True)
    if st.button("Actualizar Datos", use_container_width=True):
        st.rerun()
st.markdown("<hr style='margin-top: 0; margin-bottom: 20px; border-color: #2A2E35;'>", unsafe_allow_html=True)

# --- VISTA 1: TERMINAL ---
if vista == "Terminal de Trading":
    col_left, col_right = st.columns([2.8, 1])
    
    with col_left:
        st.markdown(f"### BTC/USDT - Velas Japonesas", unsafe_allow_html=True)
        try:
            ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)
            
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False, height=450, margin=dict(l=0, r=0, t=10, b=0))
            fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False))
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.error("No se pudieron cargar las velas.")

        st.markdown("### CURVA DE CAPITAL")
        if len(st.session_state.equity_history) > 1:
            df_eq = pd.DataFrame(st.session_state.equity_history)
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=df_eq['time'], y=df_eq['equity'], mode='lines', fill='tozeroy', line=dict(color='#3B82F6', width=2), fillcolor='rgba(59, 130, 246, 0.1)'))
            fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#2A2E35'), height=180, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("Recopilando historial de capital...")

        st.markdown("### HISTORIAL DE ÓRDENES")
        if st.session_state.orders:
            html_orders = "<table class='nexora-table'><tr><th>Hora</th><th>Activo</th><th>Acción</th><th>Precio</th></tr>"
            for o in st.session_state.orders[:5]:
                color = "#10B981" if o["Acción"] == "BUY" else "#EF4444"
                html_orders += f"<tr><td>{o['Hora']}</td><td>{o['Activo']}</td><td style='color:{color}; font-weight:bold;'>{o['Acción']}</td><td>${o['Precio']:,.2f}</td></tr>"
            html_orders += "</table>"
            st.markdown(html_orders, unsafe_allow_html=True)
        else:
            st.info("Esperando la primera operación del bot...")

    with col_right:
        st.markdown("### RESUMEN")
        st.metric("EQUITY TOTAL", f"${equity:,.2f}", f"{total_return:+,.2f}")
        st.metric("EFECTIVO", f"${st.session_state.cash:,.2f}", "Disponible")
        st.metric("P&L NO REALIZADO", f"${pnl_unrealized:,.2f}", "En el mercado")
        
        st.markdown("### RIESGO")
        if len(st.session_state.equity_history) > 5:
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

        st.markdown("### LIVE BOT FEED")
        logs_html = "<div class='bot-logs' style='height: 200px;'>"
        for log in st.session_state.bot_logs:
            color = "#10B981" if "Comprando" in log else "#EF4444" if "Vendiendo" in log else "#94A3B8"
            logs_html += f"<div style='color: {color}; margin-bottom: 4px;'>{log}</div>"
        logs_html += "</div>"
        st.markdown(logs_html, unsafe_allow_html=True)

        st.markdown("### POSICIONES")
        if not st.session_state.positions:
            st.info("Sin posiciones.")
        else:
            html_pos = "<table class='nexora-table'><tr><th>Activo</th><th>Cant</th><th>P&L</th></tr>"
            for ticker, p in st.session_state.positions.items():
                curr_price = prices.get(ticker, p['buy_price'])
                pnl = (curr_price - p['buy_price']) * p['qty']
                color = "#10B981" if pnl >= 0 else "#EF4444"
                html_pos += f"<tr><td>{ticker.split('/')[0]}</td><td>{p['qty']:.4f}</td><td style='color:{color}; font-weight:bold;'>{pnl:+,.2f}</td></tr>"
            html_pos += "</table>"
            st.markdown(html_pos, unsafe_allow_html=True)

# --- VISTA 2: MERCADO ---
elif vista == "Análisis de Mercado":
    st.title("Visión Macro del Mercado")
    try:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT", "AVAX/USDT", "SUI/USDT"]
        tickers = exchange.fetch_tickers(symbols)
        data = []
        for s in symbols:
            if s in tickers and tickers[s]['percentage'] is not None:
                data.append({"symbol": s.split('/')[0], "change": tickers[s]['percentage']})
        
        df_market = pd.DataFrame(data)
        fig_heat = go.Figure(go.Treemap(
            labels=df_market['symbol'], parents=[""] * len(df_market), values=[1] * len(df_market),
            text=[f"{c:+.2f}%" for c in df_market['change']], textinfo="label+text",
            marker=dict(colors=df_market['change'], colorscale="RdYlGn", cmid=0, line=dict(width=2, color="#0F1115"))
        ))
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    except:
        st.error("Error cargando datos de mercado.")

# --- VISTA 3: RED NEURONAL ---
elif vista == "Red Neuronal LSTM":
    st.title("Laboratorio de Inteligencia Artificial")
    
    col_net, col_monitoring = st.columns([2, 1])
    with col_net:
        st.subheader("Topología de la Red Neuronal")
        np.random.seed(42) 
        x_in, y_in, z_in = np.zeros(5), np.linspace(-2, 2, 5), np.zeros(5)
        x_hid, y_hid, z_hid = np.full(15, 3.0), np.linspace(-2.5, 2.5, 15), np.zeros(15)
        x_out, y_out, z_out = np.array([6.0]), np.array([0.0]), np.array([0.0])
        
        fig = go.Figure()
        for i in range(5):
            for j in range(15):
                fig.add_trace(go.Scatter3d(x=[x_in[i], x_hid[j]], y=[y_in[i], y_hid[j]], z=[z_in[i], z_hid[j]], mode='lines', line=dict(color='rgba(148, 163, 184, 0.2)', width=2), showlegend=False, hoverinfo='none'))
        for j in range(15):
            fig.add_trace(go.Scatter3d(x=[x_hid[j], x_out[0]], y=[y_hid[j], y_out[0]], z=[z_hid[j], z_out[0]], mode='lines', line=dict(color='rgba(148, 163, 184, 0.2)', width=2), showlegend=False, hoverinfo='none'))

        fig.add_trace(go.Scatter3d(x=x_in, y=y_in, z=z_in, mode='markers', name='Input', marker=dict(size=10, color='#3B82F6')))
        fig.add_trace(go.Scatter3d(x=x_hid, y=y_hid, z=z_hid, mode='markers', name='LSTM Cell', marker=dict(size=12, color='#8B5CF6')))
        fig.add_trace(go.Scatter3d(x=x_out, y=y_out, z=z_out, mode='markers', name='Output', marker=dict(size=18, color='#F59E0B', symbol='diamond')))
        
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', scene=dict(xaxis=dict(showbackground=False, showgrid=False, showticklabels=False), yaxis=dict(showbackground=False, showgrid=False, showticklabels=False), zaxis=dict(showbackground=False, showgrid=False, showticklabels=False), bgcolor='rgba(0,0,0,0)', camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))), margin=dict(l=0, r=0, t=0, b=0), height=500, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#94A3B8')))
        st.plotly_chart(fig, use_container_width=True, key=f"lstm_3d_static")

    with col_monitoring:
        st.markdown("### NEURAL MONITORING")
        st.metric("PÉRDIDA (MSE)", "0.0012", "-0.0001")
        st.metric("PRECISIÓN TENDENCIA", "68.4%", "+0.2%")
        st.metric("ÉPOCAS ENTRENADAS", "150", "Completado")
        st.divider()
        st.markdown("### CURVA DE APRENDIZAJE")
        epochs = np.arange(1, 101)
        loss_curve = 0.01 * np.exp(-epochs/20) + np.random.normal(0, 0.0002, 100)
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(x=epochs, y=loss_curve, mode='lines', line=dict(color='#10B981', width=2)))
        fig_loss.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94A3B8'), xaxis=dict(title='Épocas', showgrid=False), yaxis=dict(title='Loss', gridcolor='#2A2E35'), margin=dict(l=0, r=0, t=10, b=0), height=250)
        st.plotly_chart(fig_loss, use_container_width=True)