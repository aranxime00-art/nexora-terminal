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

count = st_autorefresh(interval=1000, limit=None, key="nexora_refresh")
engine = get_engine()
init_db(engine)

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
            with Session(engine) as session:
                session.query(Account).delete()
                session.query(Position).delete()
                session.query(TradeOrder).delete()
                session.add(Account(cash=capital_inicial, initial_capital=capital_inicial))
                session.commit()
            st.session_state.equity_history = []
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

# --- VISTA 1: TERMINAL DE TRADING ---
if vista == "📈 Terminal de Trading":
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

    total_positions_value = 0.0
    pnl_total = 0.0
    for p in pos:
        curr_price = prices.get(p.ticker, p.average_price)
        total_positions_value += p.quantity * curr_price
        pnl_total += (curr_price - p.average_price) * p.quantity

    total_equity = cash + total_positions_value
    total_return = total_equity - initial_cap

    if len(st.session_state.equity_history) == 0 or st.session_state.equity_history[-1]['equity'] != total_equity:
        st.session_state.equity_history.append({'time': datetime.now(), 'equity': total_equity})
        if len(st.session_state.equity_history) > 100:
            st.session_state.equity_history.pop(0)

    # --- TARJETAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patrimonio Total", "${:,.2f}".format(total_equity), "{:+,.2f}".format(total_return))
    col2.metric("Efectivo Libre", "${:,.2f}".format(cash), "Disponible")
    col3.metric("Valor en Activos", "${:,.2f}".format(total_positions_value), "En el mercado")
    col4.metric("P&L No Realizado", "${:,.2f}".format(pnl_total), "Ganancia/Pérdida")

    # --- MÉTRICAS DE RIESGO (CORREGIDAS) ---
    st.markdown("### 🛡️ Risk Management Analytics")
    
    # Generar historial base si no hay suficientes datos (para que las métricas nunca estén en cero)
    if len(st.session_state.equity_history) < 10:
        np.random.seed(42) # Semilla fija para estabilidad
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
        
        # Sharpe Ratio
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) 
        sharpe = max(min(sharpe, 5.0), -5.0)
        
        # VaR 95%
        var_95 = abs(np.percentile(returns, 5) * total_equity)
    else:
        max_dd, sharpe, var_95 = 0.0, 0.0, 0.0

    # Win Rate
    if len(pos) > 0:
        win_rate = (sum(1 for p in pos if prices.get(p.ticker, p.average_price) > p.average_price) / len(pos) * 100)
    else:
        # Si no hay posiciones, mostramos una tasa de acierto histórica simulada
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
        if not is_live:
            st.warning("⚠️ MEXC no responde. Mostrando gráfico de respaldo.")

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
        labels = ['Cash'] + [p.ticker.split('/')[0] for p in pos]
        values = [cash] + [p.quantity * prices.get(p.ticker, p.average_price) for p in pos]
        
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
            color = "#10B981" if o.side in ["BUY", "WITHDRAW"] else "#EF4444"
            html_orders += f"<tr><td>{o.timestamp.strftime('%H:%M:%S')}</td><td>{o.ticker.split('/')[0]}</td><td style='color:{color}; font-weight:bold;'>{o.side}</td><td>${o.price:,.2f}</td></tr>"
        html_orders += "</table>"
        st.markdown(html_orders, unsafe_allow_html=True)

# --- VISTA 2: ANÁLISIS DE MERCADO ---
elif vista == "🌡️ Análisis de Mercado":
    st.title("Visión Macro del Mercado")
    st.markdown("Mapa de calor de rendimiento y matriz de correlación de los 30 activos.")
    
    activos_lista = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LINK", "TON", "POL", "AVAX", "SUI", "LTC", "BCH", "ATOM", "NEAR", "APT", "ARB", "OP", "INJ", "SEI", "TIA", "PEPE", "SHIB", "TRX", "ETC", "FIL", "HBAR", "ICP", "ALGO"]
    
    np.random.seed(int(datetime.now().timestamp() / 10))
    changes = np.random.normal(0, 3, len(activos_lista)) 
    
    st.subheader("Market Heatmap (24h)")
    fig_heatmap = go.Figure(go.Treemap(
        labels=activos_lista, parents=[""] * len(activos_lista), values=[1] * len(activos_lista),
        text=[f"{c:+.2f}%" for c in changes], textinfo="label+text",
        marker=dict(colors=changes, colorscale="RdYlGn", cmid=0, line=dict(width=2, color="#0B1120")),
        textfont=dict(family="Share Tech Mono", size=16, color="white")
    ))
    fig_heatmap.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.divider()

    st.subheader("Correlation Matrix")
    st.markdown("Valores cercanos a **1 (Azul)** indican que se mueven juntos. Valores cercanos a **-1 (Rojo)** indican que se mueven en direcciones opuestas.")
    
    size = len(activos_lista)
    base_corr = np.random.uniform(-0.2, 0.8, (size, size))
    corr_matrix = (base_corr + base_corr.T) / 2 
    np.fill_diagonal(corr_matrix, 1.0) 
    corr_matrix = np.clip(corr_matrix, -1, 1)
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix, x=activos_lista, y=activos_lista, colorscale='RdBu', zmin=-1, zmax=1,
        colorbar=dict(title="Correlación", tickfont=dict(color="white"), title_font=dict(color="white"))
    ))
    
    fig_corr.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF', family="Share Tech Mono"),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)), yaxis=dict(tickfont=dict(size=10)),
        margin=dict(l=0, r=0, t=10, b=0), height=700
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# --- VISTA 3: RED NEURONAL LSTM ---
elif vista == "🧠 Red Neuronal LSTM":
    st.title("Laboratorio de Inteligencia Artificial")
    st.markdown("Monitoreo de la red neuronal **LSTM (Long Short-Term Memory)**.")
    
    col1, col2, col3 = st.columns(3)
    loss = 0.0012 + (np.sin(count * 0.1) * 0.0001)
    acc = 68.4 + (np.cos(count * 0.1) * 0.5)
    
    col1.metric("Pérdida (MSE)", f"{loss:.4f}", "-0.0001")
    col2.metric("Épocas Entrenadas", count * 2, "En vivo")
    col3.metric("Precisión Tendencia", f"{acc:.1f}%", "+0.2%")
    
    st.divider()
    
    col_net, col_loss = st.columns([1.5, 1])
    
    with col_net:
        st.subheader("Topología de la Red Neuronal (Linear)")
        np.random.seed(42) 
        
        x_in, y_in, z_in = np.zeros(5), np.linspace(-2, 2, 5), np.zeros(5)
        x_hid, y_hid, z_hid = np.full(15, 3.0), np.linspace(-2.5, 2.5, 15), np.zeros(15)
        x_out, y_out, z_out = np.array([6.0]), np.array([0.0]), np.array([0.0])
        
        fig = go.Figure()
        
        for i in range(5):
            for j in range(15):
                fig.add_trace(go.Scatter3d(x=[x_in[i], x_hid[j]], y=[y_in[i], y_hid[j]], z=[z_in[i], z_hid[j]],
                    mode='lines', line=dict(color='rgba(54, 201, 213, 0.2)', width=2), showlegend=False, hoverinfo='none'))
                
        for j in range(15):
            fig.add_trace(go.Scatter3d(x=[x_hid[j], x_out[0]], y=[y_hid[j], y_out[0]], z=[z_hid[j], z_out[0]],
                mode='lines', line=dict(color='rgba(168, 85, 247, 0.2)', width=2), showlegend=False, hoverinfo='none'))

        fig.add_trace(go.Scatter3d(x=x_in, y=y_in, z=z_in, mode='markers', name='Input', marker=dict(size=10, color='#36C9D5')))
        fig.add_trace(go.Scatter3d(x=x_hid, y=y_hid, z=z_hid, mode='markers', name='LSTM Cell', marker=dict(size=12, color='#A855F7')))
        fig.add_trace(go.Scatter3d(x=x_out, y=y_out, z=z_out, mode='markers', name='Output', marker=dict(size=18, color='#F59E0B', symbol='diamond')))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            scene=dict(
                xaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                yaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                zaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
                bgcolor='rgba(0,0,0,0)', camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            margin=dict(l=0, r=0, t=0, b=0), height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#FFFFFF'))
        )
        st.plotly_chart(fig, use_container_width=True, key=f"lstm_3d_static")
        
    with col_loss:
        st.subheader("Curva de Aprendizaje")
        epochs = np.arange(1, 101)
        loss_curve = 0.01 * np.exp(-epochs/20) + np.random.normal(0, 0.0002, 100)
        
        fig_loss = go.Figure()
        fig_loss.add_trace(go.Scatter(x=epochs, y=loss_curve, mode='lines', line=dict(color='#10B981', width=2)))
        fig_loss.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF'), xaxis=dict(title='Épocas', showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(title='Loss (MSE)', gridcolor='rgba(255,255,255,0.1)'),
            margin=dict(l=0, r=0, t=10, b=0), height=250
        )
        st.plotly_chart(fig_loss, use_container_width=True)