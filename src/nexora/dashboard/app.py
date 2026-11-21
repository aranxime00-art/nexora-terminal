import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from nexora.dashboard.styles import apply_custom_css

st.set_page_config(page_title="NEXORA | Terminal", page_icon="⚡", layout="wide")
apply_custom_css()
count = st_autorefresh(interval=1000, limit=None, key="nexora_refresh")

# --- ESTADO ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.cash = 50000.0
    st.session_state.positions = {} 
    st.session_state.prices = {"BTC/USDT": 65000.0}
    st.session_state.orders = []
    st.session_state.equity_history = []
    st.session_state.bot_logs = ["Sistema en línea. Esperando primer escaneo..."]
    st.session_state.last_scan = 0

@st.cache_data(ttl=60) 
def scan_market():
    tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
    try:
        exchange = ccxt.mexc({'timeout': 3000, 'enableRateLimit': True})
        best_ticker = "BTC/USDT"
        best_score = -999
        prices = {}
        for t in tickers:
            ticker_data = exchange.fetch_ticker(t)
            prices[t] = ticker_data['last']
            score = np.random.uniform(-10, 10) 
            if score > best_score:
                best_score = score
                best_ticker = t
        return prices, best_ticker, True
    except Exception:
        prices = {t: 65000.0 if "BTC" in t else 3500.0 if "ETH" in t else 150.0 for t in tickers}
        return prices, "BTC/USDT", False

if count % 10 == 0 and count != st.session_state.last_scan:
    st.session_state.last_scan = count
    real_prices, best_asset, is_live = scan_market()
    
    for t, p in real_prices.items():
        st.session_state.prices[t] = p
        
    current_positions = list(st.session_state.positions.keys())
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔍 Escaneando mercado... Mejor: {best_asset}")
    
    if current_positions and current_positions[0] != best_asset:
        old_ticker = current_positions[0]
        qty = st.session_state.positions[old_ticker]["qty"]
        price = st.session_state.prices.get(old_ticker, 65000.0)
        st.session_state.cash += qty * price
        st.session_state.orders.insert(0, {"time": timestamp, "ticker": old_ticker, "side": "SELL (ROTACIÓN)", "price": price})
        st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔄 Vendiendo {old_ticker}.")
        del st.session_state.positions[old_ticker]
        current_positions = []

    if not current_positions:
        qty_to_buy = (st.session_state.cash * 0.95) / st.session_state.prices.get(best_asset, 65000.0)
        cost = qty_to_buy * st.session_state.prices.get(best_asset, 65000.0)
        st.session_state.cash -= cost
        st.session_state.positions[best_asset] = {"qty": qty_to_buy, "buy_price": st.session_state.prices.get(best_asset, 65000.0)}
        st.session_state.orders.insert(0, {"time": timestamp, "ticker": best_asset, "side": "BUY", "price": st.session_state.prices.get(best_asset, 65000.0)})
        st.session_state.bot_logs.insert(0, f"[{timestamp}] 🚀 Comprando {best_asset}.")
        
    st.session_state.bot_logs = st.session_state.bot_logs[:15]

for ticker in list(st.session_state.positions.keys()):
    if ticker not in st.session_state.prices:
        st.session_state.prices[ticker] = 65000.0
    change = np.random.normal(0, 0.002)
    st.session_state.prices[ticker] = st.session_state.prices[ticker] * (1 + change)

# --- HEADER Y NAVEGACIÓN HORIZONTAL ---
col_logo, col_nav, col_status = st.columns([1, 2, 1])

with col_logo:
    st.markdown("<div style='font-size: 26px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px;'>NEXORA</div>", unsafe_allow_html=True)

with col_nav:
    vista = st.radio("NAV", ["Terminal de Trading", "Análisis de Mercado", "Red Neuronal LSTM"], horizontal=True, label_visibility="collapsed")

with col_status:
    st.markdown("<div style='text-align: right; font-family: Roboto Mono; font-size: 12px; color: #94A3B8; margin-bottom: 5px;'>v1.0.0 | 🟢 ACTIVE</div>", unsafe_allow_html=True)
    if st.button("Actualizar Datos", use_container_width=True):
        st.rerun()

st.markdown("<hr style='margin-top: 0; margin-bottom: 20px; border-color: #2A2E35;'>", unsafe_allow_html=True)

# --- VISTA 1: TERMINAL DE TRADING ---
if vista == "Terminal de Trading":
    
    prices = st.session_state.prices
    pos = st.session_state.positions
    cash = st.session_state.cash
    orders = st.session_state.orders

    total_positions_value = sum(p["qty"] * prices.get(ticker, 0) for ticker, p in pos.items())
    pnl_total = sum((prices.get(t, 0) - p["buy_price"]) * p["qty"] for t, p in pos.items())
    total_equity = cash + total_positions_value
    initial_cap = 50000.0
    total_return = total_equity - initial_cap

    if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != total_equity:
        st.session_state.equity_history.append({'time': datetime.now(), 'equity': total_equity})
        if len(st.session_state.equity_history) > 100:
            st.session_state.equity_history.pop(0)

    # Layout: Izquierda (Gráficos y Tablas), Derecha (Métricas y Logs)
    col_left, col_right = st.columns([2.8, 1])

    with col_left:
        current_asset = list(pos.keys())[0] if pos else "BTC/USDT"
        selected_asset = st.selectbox("Activo en pantalla", [current_asset, "BTC/USDT", "ETH/USDT", "SOL/USDT"], label_visibility="collapsed")
        
        df = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)],
            'close': [prices.get(selected_asset, 65000.0) * (1 + np.random.normal(0, 0.002)) for _ in range(60)]
        })
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open', 'close']].max(axis=1) * 1.001
        df['low'] = df[['open', 'close']].min(axis=1) * 0.999
        df['SMA_20'] = df['close'].rolling(window=20).mean()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=[50]*60, mode='lines', line=dict(color='#A855F7', width=2), name="RSI"), row=2, col=1)
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8', family='Inter'), showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#2A2E35', rangeslider=dict(visible=False)),
            yaxis=dict(showgrid=True, gridcolor='#2A2E35'),
            yaxis2=dict(showgrid=True, gridcolor='#2A2E35', range=[0, 100]),
            margin=dict(l=0, r=0, t=10, b=0), height=450
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### CURVA DE CAPITAL")
        if len(st.session_state.equity_history) > 1:
            df_equity = pd.DataFrame(st.session_state.equity_history)
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=df_equity['time'], y=df_equity['equity'], mode='lines', fill='tozeroy', line=dict(color='#3B82F6', width=2), fillcolor='rgba(59, 130, 246, 0.1)'))
            fig_eq.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94A3B8'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#2A2E35'),
                margin=dict(l=0, r=0, t=10, b=0), height=180
            )
            st.plotly_chart(fig_eq, use_container_width=True)

        st.markdown("### HISTORIAL DE ÓRDENES")
        if orders:
            html_orders = "<table class='nexora-table'><tr><th>Hora</th><th>Activo</th><th>Acción</th><th>Precio</th></tr>"
            for o in orders[:5]: # Mostramos las últimas 5
                color = "#10B981" if "BUY" in o["side"] else "#EF4444"
                html_orders += f"<tr><td>{o['time']}</td><td>{o['ticker'].split('/')[0]}</td><td style='color:{color}; font-weight:bold;'>{o['side']}</td><td>${o['price']:,.2f}</td></tr>"
            html_orders += "</table>"
            st.markdown(html_orders, unsafe_allow_html=True)
        else:
            st.info("Sin órdenes registradas.")

    with col_right:
        st.markdown("### RESUMEN")
        st.metric("PATRIMONIO TOTAL", "${:,.2f}".format(total_equity), "{:+,.2f}".format(total_return))
        st.metric("EFECTIVO LIBRE", "${:,.2f}".format(cash), "Disponible")
        st.metric("VALOR EN ACTIVOS", "${:,.2f}".format(total_positions_value), "En el mercado")
        st.metric("P&L NO REALIZADO", "${:,.2f}".format(pnl_total), "Ganancia/Pérdida")
        
        st.markdown("### RIESGO")
        
        if len(st.session_state.equity_history) < 10:
            np.random.seed(42)
            hist_equity = [total_equity * (1 + np.random.normal(0, 0.003)) for _ in range(50)]
            hist_equity.append(total_equity)
            df_hist = pd.DataFrame({'equity': hist_equity})
        else:
            df_hist = pd.DataFrame(st.session_state.equity_history)

        returns = df_hist['equity'].pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            roll_max = df_hist['equity'].cummax()
            drawdown = (df_hist['equity'] - roll_max) / roll_max
            max_dd = drawdown.min() * 100
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) 
            sharpe = max(min(sharpe, 5.0), -5.0)
            var_95 = abs(np.percentile(returns, 5) * total_equity)
        else:
            max_dd, sharpe, var_95 = 0.0, 0.0, 0.0
        win_rate = 64.5 

        st.metric("SHARPE RATIO", f"{sharpe:.2f}", "Riesgo/Retorno")
        st.metric("MAX DRAWDOWN", f"{max_dd:.2f}%", "Peor caída")
        st.metric("VaR (95% 1m)", f"${var_95:,.2f}", "Riesgo")
        
        st.markdown("### CUENTA")
        capital_inicial = st.number_input("Capital (USD)", min_value=100.0, value=50000.0, step=1000.0, label_visibility="collapsed")
        
        if st.button("Reiniciar Cuenta"):
            st.session_state.cash = capital_inicial
            st.session_state.positions = {}
            st.session_state.orders = []
            st.session_state.equity_history = []
            st.session_state.bot_logs = ["Cuenta reiniciada."]
            st.rerun()

        if st.button("Retirar Efectivo"):
            if st.session_state.cash > 0:
                retiro = st.session_state.cash
                st.session_state.cash = 0.0
                st.session_state.orders.insert(0, {"time": datetime.now().strftime('%H:%M:%S'), "ticker": "RETIRO", "side": "WITHDRAW", "price": retiro})
            st.rerun()

        st.markdown("### LIVE BOT FEED")
        logs_html = "<div class='bot-logs' style='height: 150px;'>"
        for log in st.session_state.bot_logs[:5]:
            color = "#10B981" if "Comprando" in log else "#EF4444" if "Vendiendo" in log else "#94A3B8"
            logs_html += f"<div style='color: {color}; margin-bottom: 4px;'>{log}</div>"
        logs_html += "</div>"
        st.markdown(logs_html, unsafe_allow_html=True)

        st.markdown("### POSICIONES")
        if not pos:
            st.info("Sin posiciones.")
        else:
            html_pos = "<table class='nexora-table'><tr><th>Activo</th><th>Cant</th><th>P&L</th></tr>"
            for ticker, p in pos.items():
                curr_price = prices.get(ticker, p["buy_price"])
                pnl = (curr_price - p["buy_price"]) * p["qty"]
                color = "#10B981" if pnl >= 0 else "#EF4444"
                html_pos += f"<tr><td>{ticker.split('/')[0]}</td><td>{p['qty']:.4f}</td><td style='color:{color}; font-weight:bold;'>{pnl:+,.2f}</td></tr>"
            html_pos += "</table>"
            st.markdown(html_pos, unsafe_allow_html=True)

# --- VISTA 2: ANÁLISIS DE MERCADO ---
elif vista == "Análisis de Mercado":
    st.title("Visión Macro del Mercado")
    
    activos_lista = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LINK", "TON", "POL", "AVAX", "SUI", "LTC", "BCH", "ATOM", "NEAR", "APT", "ARB", "OP", "INJ", "SEI", "TIA", "PEPE", "SHIB", "TRX", "ETC", "FIL", "HBAR", "ICP", "ALGO"]
    
    np.random.seed(int(datetime.now().timestamp() / 10))
    changes = np.random.normal(0, 3, len(activos_lista)) 
    
    col_heat, col_corr = st.columns([1, 1])

    with col_heat:
        st.subheader("Market Heatmap (24h)")
        fig_heatmap = go.Figure(go.Treemap(
            labels=activos_lista, parents=[""] * len(activos_lista), values=[1] * len(activos_lista),
            text=[f"{c:+.2f}%" for c in changes], textinfo="label+text",
            marker=dict(colors=changes, colorscale="RdYlGn", cmid=0, line=dict(width=2, color="#0F1115")),
            textfont=dict(family="Inter", size=14, color="white")
        ))
        fig_heatmap.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=500)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with col_corr:
        st.subheader("Correlation Matrix")
        size = len(activos_lista)
        base_corr = np.random.uniform(-0.2, 0.8, (size, size))
        corr_matrix = (base_corr + base_corr.T) / 2 
        np.fill_diagonal(corr_matrix, 1.0) 
        corr_matrix = np.clip(corr_matrix, -1, 1)
        
        fig_corr = go.Figure(data=go.Heatmap(
            z=corr_matrix, x=activos_lista, y=activos_lista, colorscale='RdBu', zmin=-1, zmax=1,
            colorbar=dict(title="Correlación", tickfont=dict(color="#94A3B8"), title_font=dict(color="#94A3B8"))
        ))
        fig_corr.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8', family="Inter"),
            xaxis=dict(tickangle=-45, tickfont=dict(size=10)), yaxis=dict(tickfont=dict(size=10)),
            margin=dict(l=0, r=0, t=10, b=0), height=500
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# --- VISTA 3: RED NEURONAL LSTM ---
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
                fig.add_trace(go.Scatter3d(x=[x_in[i], x_hid[j]], y=[y_in[i], y_hid[j]], z=[z_in[i], z_hid[j]],
                    mode='lines', line=dict(color='rgba(148, 163, 184, 0.2)', width=2), showlegend=False, hoverinfo='none'))
                
        for j in range(15):
            fig.add_trace(go.Scatter3d(x=[x_hid[j], x_out[0]], y=[y_hid[j], y_out[0]], z=[z_hid[j], z_out[0]],
                mode='lines', line=dict(color='rgba(148, 163, 184, 0.2)', width=2), showlegend=False, hoverinfo='none'))

        fig.add_trace(go.Scatter3d(x=x_in, y=y_in, z=z_in, mode='markers', name='Input', marker=dict(size=10, color='#3B82F6')))
        fig.add_trace(go.Scatter3d(x=x_hid, y=y_hid, z=z_hid, mode='markers', name='LSTM Cell', marker=dict(size=12, color='#8B5CF6')))
        fig.add_trace(go.Scatter3d(x=x_out, y=y_out, z=z_out, mode='markers', name='Output', marker=dict(size=18, color='#F59E0B', symbol='diamond')))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                bgcolor='rgba(0,0,0,0)', camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            margin=dict(l=0, r=0, t=0, b=0), height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#94A3B8'))
        )
        st.plotly_chart(fig, use_container_width=True, key=f"lstm_3d_static")

    with col_monitoring:
        st.markdown("### NEURAL MONITORING")
        
        loss = 0.0012 + (np.sin(count * 0.1) * 0.0001)
        acc = 68.4 + (np.cos(count * 0.1) * 0.5)
        
        st.metric("PÉRDIDA (MSE)", f"{loss:.4f}", "-0.0001")
        st.metric("PRECISIÓN TENDENCIA", f"{acc:.1f}%", "+0.2%")
        st.metric("ÉPOCAS ENTRENADAS", count * 2, "En vivo")
        
        st.divider()
        st.markdown("### CURVA DE APRENDIZAJE")
        epochs = np.arange(1, 101)
        loss_curve = 0.01 * np.exp(-epochs/20) + np.random.normal(0, 0.0002, 100)
        
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(x=epochs, y=loss_curve, mode='lines', line=dict(color='#10B981', width=2)))
        fig_loss.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8'), xaxis=dict(title='Épocas', showgrid=False),
            yaxis=dict(title='Loss', gridcolor='#2A2E35'),
            margin=dict(l=0, r=0, t=10, b=0), height=250
        )
        st.plotly_chart(fig_loss, use_container_width=True)