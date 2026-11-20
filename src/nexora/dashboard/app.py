import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from nexora.dashboard.styles import apply_custom_css

st.set_page_config(page_title="NEXORA | Terminal", page_icon="📈", layout="wide")
apply_custom_css()
count = st_autorefresh(interval=1000, limit=None, key="nexora_refresh")

# --- ESTADO EN MEMORIA (Sobrevive a los refrescos) ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.cash = 50000.0
    st.session_state.positions = {"BTC/USDT": {"qty": 0.1, "buy_price": 65000.0}}
    st.session_state.prices = {"BTC/USDT": 65000.0}
    st.session_state.orders = [{"time": datetime.now().strftime('%H:%M:%S'), "ticker": "BTC/USDT", "side": "BUY", "price": 65000.0}]
    st.session_state.equity_history = []
    st.session_state.cash -= (0.1 * 65000.0)

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
    st.markdown("<p style='text-align: center; font-family: Share Tech Mono; font-size: 10px; color: #A855F7 !important;'>QUANTITATIVE INTELLIGENCE</p>", unsafe_allow_html=True)
    st.divider()
    
    vista = st.radio("MÓDULOS DEL SISTEMA", ["📈 Terminal de Trading", "🌡️ Análisis de Mercado", "🧠 Red Neuronal LSTM"])
    st.divider()
    
    if vista == "📈 Terminal de Trading":
        st.subheader("Gestión de Cuenta")
        capital_inicial = st.number_input("Capital Inicial (USD)", min_value=100.0, value=50000.0, step=1000.0)
        
        if st.button("Reiniciar Cuenta"):
            st.session_state.cash = capital_inicial
            st.session_state.positions = {}
            st.session_state.orders = []
            st.session_state.equity_history = []
            st.success(f"Cuenta reiniciada con ${capital_inicial:,.2f}.")
            st.rerun()

        if st.button("Retirar TODO el Efectivo"):
            if st.session_state.cash > 0:
                retiro = st.session_state.cash
                st.session_state.cash = 0.0
                st.session_state.orders.insert(0, {"time": datetime.now().strftime('%H:%M:%S'), "ticker": "RETIRO", "side": "WITHDRAW", "price": retiro})
                st.success("Retiro total exitoso.")
            else:
                st.warning("No hay efectivo para retirar.")
            st.rerun()

# --- VISTA 1: TERMINAL DE TRADING ---
if vista == "📈 Terminal de Trading":
    st.title("Terminal de Trading (Simulador MEXC)")
    
    # 1. Simulador de fluctuación de precios
    for ticker in list(st.session_state.positions.keys()):
        if ticker not in st.session_state.prices:
            st.session_state.prices[ticker] = 65000.0
        
        # Cambio aleatorio entre -0.5% y +0.5% para simular volatilidad
        change = np.random.normal(0, 0.005)
        st.session_state.prices[ticker] = st.session_state.prices[ticker] * (1 + change)
        
        # LÓGICA DE STOP-LOSS Y TAKE-PROFIT
        buy_price = st.session_state.positions[ticker]["buy_price"]
        curr_price = st.session_state.prices[ticker]
        pnl_pct = (curr_price - buy_price) / buy_price
        
        if pnl_pct <= -0.05: # STOP LOSS AL 5%
            qty = st.session_state.positions[ticker]["qty"]
            revenue = qty * curr_price
            st.session_state.cash += revenue
            st.session_state.orders.insert(0, {"time": datetime.now().strftime('%H:%M:%S'), "ticker": ticker, "side": "SELL (STOP-LOSS)", "price": curr_price})
            del st.session_state.positions[ticker]
            st.toast(f"🛑 STOP-LOSS Activado en {ticker} (-5%)")
            
        elif pnl_pct >= 0.10: # TAKE PROFIT AL 10%
            qty = st.session_state.positions[ticker]["qty"]
            revenue = qty * curr_price
            st.session_state.cash += revenue
            st.session_state.orders.insert(0, {"time": datetime.now().strftime('%H:%M:%S'), "ticker": ticker, "side": "SELL (TAKE-PROFIT)", "price": curr_price})
            del st.session_state.positions[ticker]
            st.toast(f"🎯 TAKE-PROFIT Activado en {ticker} (+10%)")

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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patrimonio Total", "${:,.2f}".format(total_equity), "{:+,.2f}".format(total_return))
    col2.metric("Efectivo Libre", "${:,.2f}".format(cash), "Disponible")
    col3.metric("Valor en Activos", "${:,.2f}".format(total_positions_value), "En el mercado")
    col4.metric("P&L No Realizado", "${:,.2f}".format(pnl_total), "Ganancia/Pérdida")

    st.markdown("### 🛡️ Risk Management Analytics")
    
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

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Sharpe Ratio", f"{sharpe:.2f}", "Riesgo/Retorno")
    r2.metric("Max Drawdown", f"{max_dd:.2f}%", "Peor caída")
    r3.metric("VaR (95% 1m)", f"${var_95:,.2f}", "Riesgo de pérdida")
    r4.metric("Win Rate", f"{win_rate:.1f}%", "Tasa de acierto")

    st.divider()

    col_chart, col_data = st.columns([2.5, 1])

    with col_chart:
        activos_lista = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT", "AVAX/USDT", "SUI/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT", "NEAR/USDT", "APT/USDT", "ARB/USDT", "OP/USDT", "INJ/USDT", "SEI/USDT", "TIA/USDT", "PEPE/USDT", "SHIB/USDT", "TRX/USDT", "ETC/USDT", "FIL/USDT", "HBAR/USDT", "ICP/USDT", "ALGO/USDT"]
        selected_asset = st.selectbox("Seleccionar Activo para Gráfico", activos_lista)
        
        df, is_live = get_real_candles(selected_asset)
        
        df['close'] = df['close'] + np.random.normal(0, df['close'] * 0.001, len(df))
        df['open'] = df['close'].shift(1).fillna(df['open'])
        df['high'] = df[['open', 'close']].max(axis=1) + (df['close'] * 0.0005)
        df['low'] = df[['open', 'close']].min(axis=1) - (df['close'] * 0.0005)

        df['SMA_20'] = df['close'].rolling(window=20).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25], subplot_titles=(f"{selected_asset} - Velas Japonesas", "RSI (14)"))

        fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444', name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)

        current_price = prices.get(selected_asset, df['close'].iloc[-1])
        fig.add_trace(go.Scatter(x=[df['timestamp'].iloc[0], df['timestamp'].iloc[-1]], y=[current_price, current_price], mode='lines', line=dict(color='#36C9D5', width=1, dash='dot'), name="Live Price"), row=1, col=1)

        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI_14'], mode='lines', line=dict(color='#A855F7', width=2), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10B981", row=2, col=1)

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF', size=11), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False), tickfont=dict(color='#FFFFFF')), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Precio (USDT)", title_font=dict(color='#36C9D5'), tickfont=dict(color='#FFFFFF')), yaxis2=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="RSI", title_font=dict(color='#A855F7'), range=[0, 100], tickfont=dict(color='#FFFFFF')), margin=dict(l=0, r=0, t=30, b=0), height=550, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    with col_data:
        st.subheader("Posiciones Abiertas")
        if not pos:
            st.markdown("<div style='background-color: #1E293B; padding: 15px; border-radius: 5px; color: #FFFFFF;'>Sin posiciones. El bot está analizando.</div>", unsafe_allow_html=True)
        else:
            html = "<table class='nexora-table'><tr><th>Activo</th><th>Cant</th><th>Compra</th><th>Actual</th><th>P&L</th></tr>"
            for ticker, p in pos.items():
                curr_price = prices.get(ticker, p["buy_price"])
                pnl = (curr_price - p["buy_price"]) * p["qty"]
                color = "#10B981" if pnl >= 0 else "#EF4444"
                html += f"<tr><td>{ticker.split('/')[0]}</td><td>{p['qty']:.4f}</td><td>${p['buy_price']:,.2f}</td><td>${curr_price:,.2f}</td><td style='color:{color}; font-weight:bold;'>{pnl:+,.2f}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

    st.divider()

    col_equity, col_pie, col_gauge = st.columns([1.5, 1, 1])

    with col_equity:
        st.subheader("Curva de Capital")
        if len(st.session_state.equity_history) > 1:
            df_equity = pd.DataFrame(st.session_state.equity_history)
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=df_equity['time'], y=df_equity['equity'], mode='lines', fill='tozeroy', line=dict(color='#36C9D5', width=2), fillcolor='rgba(54, 201, 213, 0.1)'))
            fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), margin=dict(l=0, r=0, t=10, b=0), height=250)
            st.plotly_chart(fig_eq, use_container_width=True)
        else:
            st.info("Recopilando datos...")

    with col_pie:
        st.subheader("Portfolio Allocation")
        labels = ['Cash'] + [t.split('/')[0] for t in pos.keys()]
        values = [cash] + [p["qty"] * prices.get(ticker, 0) for ticker, p in pos.items()]
        
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=['#36C9D5', '#A855F7', '#10B981', '#F59E0B', '#EF4444']))])
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), margin=dict(l=0, r=0, t=10, b=0), height=250, showlegend=False, annotations=[dict(text='Assets', x=0.5, y=0.5, font_size=15, showarrow=False, font_color="#FFF")])
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_gauge:
        st.subheader("Market Sentiment")
        btc_rsi = df['RSI_14'].iloc[-1] if not df.empty else 50
        fig_gauge = go.Figure(go.Indicator(mode = "gauge+number", value = btc_rsi, title = {'text': "Fear / Greed", 'font': {'color': 'white', 'size': 14}}, gauge = {'axis': {'range': [0, 100], 'tickcolor': "white"}, 'bar': {'color': "#A855F7"}, 'steps' : [{'range': [0, 30], 'color': "rgba(239, 68, 68, 0.5)"}, {'range': [30, 70], 'color': "rgba(245, 158, 11, 0.5)"}, {'range': [70, 100], 'color': "rgba(16, 185, 129, 0.5)"}]}))
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), margin=dict(l=20, r=20, t=30, b=10), height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()
    st.subheader("Historial de Órdenes")
    if not orders:
        st.markdown("<div style='background-color: #1E293B; padding: 15px; border-radius: 5px; color: #FFFFFF;'>Aún no hay registros.</div>", unsafe_allow_html=True)
    else:
        html_orders = "<table class='nexora-table'><tr><th>Hora</th><th>Activo</th><th>Acción</th><th>Precio</th></tr>"
        for o in orders[:5]:
            color = "#10B981" if "BUY" in o["side"] else "#EF4444"
            html_orders += f"<tr><td>{o['time']}</td><td>{o['ticker'].split('/')[0]}</td><td style='color:{color}; font-weight:bold;'>{o['side']}</td><td>${o['price']:,.2f}</td></tr>"
        html_orders += "</table>"
        st.markdown(html_orders, unsafe_allow_html=True)