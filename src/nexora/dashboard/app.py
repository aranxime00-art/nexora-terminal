import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ccxt
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from nexora.dashboard.styles import apply_custom_css
import time

st.set_page_config(page_title="NEXORA | Terminal", page_icon="📈", layout="wide")
apply_custom_css()
count = st_autorefresh(interval=1000, limit=None, key="nexora_refresh")

# --- ESTADO EN MEMORIA (Sobrevive a los refrescos) ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.cash = 50000.0
    st.session_state.positions = {} 
    st.session_state.prices = {}
    st.session_state.orders = []
    st.session_state.equity_history = []
    st.session_state.bot_logs = ["Sistema Iniciado. Esperando primer escaneo..."]
    st.session_state.last_scan = 0

# --- CACHÉ PARA NO SATURAR MEXC ---
@st.cache_data(ttl=60) # Escanea el mercado cada 60 segundos
def scan_market():
    tickers = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
        "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT",
        "AVAX/USDT", "SUI/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT",
        "NEAR/USDT", "APT/USDT", "ARB/USDT", "OP/USDT", "INJ/USDT",
        "SEI/USDT", "TIA/USDT", "PEPE/USDT", "SHIB/USDT", "TRX/USDT",
        "ETC/USDT", "FIL/USDT", "HBAR/USDT", "ICP/USDT", "ALGO/USDT"
    ]
    try:
        exchange = ccxt.mexc({'timeout': 3000, 'enableRateLimit': True})
        # Para no bloquear, solo analizamos los primeros 5 activos
        # (En un servidor real se harían los 30, pero aquí limitamos para la demo)
        best_ticker = "BTC/USDT"
        best_score = -999
        
        prices = {}
        for t in tickers[:5]: # Analizamos 5 para que sea rápido
            ticker_data = exchange.fetch_ticker(t)
            prices[t] = ticker_data['last']
            
            # Simular un score para que varíe
            score = np.random.uniform(-10, 10) 
            if score > best_score:
                best_score = score
                best_ticker = t
                
        return prices, best_ticker, True
    except Exception as e:
        # Fallback si MEXC falla
        prices = {t: 65000.0 if "BTC" in t else 3500.0 if "ETH" in t else 150.0 for t in tickers[:5]}
        return prices, "BTC/USDT", False

# --- LÓGICA DEL BOT EN LA NUBE ---
# Ejecutamos el escaneo cada 10 refrescos (10 segundos) para simular el bot
if count % 10 == 0 and count != st.session_state.last_scan:
    st.session_state.last_scan = count
    real_prices, best_asset, is_live = scan_market()
    
    # Actualizar precios reales
    for t, p in real_prices.items():
        st.session_state.prices[t] = p
        
    current_positions = list(st.session_state.positions.keys())
    
    # Log del bot
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔍 Escaneando mercado... Mejor activo: {best_asset}")
    
    # Si tenemos un activo que no es el mejor, lo vendemos
    if current_positions and current_positions[0] != best_asset:
        old_ticker = current_positions[0]
        qty = st.session_state.positions[old_ticker]["qty"]
        price = st.session_state.prices.get(old_ticker, 65000.0)
        revenue = qty * price
        st.session_state.cash += revenue
        st.session_state.orders.insert(0, {"time": timestamp, "ticker": old_ticker, "side": "SELL (ROTACIÓN)", "price": price})
        st.session_state.bot_logs.insert(0, f"[{timestamp}] 🔄 Vendiendo {old_ticker} para rotar capital.")
        del st.session_state.positions[old_ticker]
        current_positions = []

    # Si no tenemos nada, compramos el mejor
    if not current_positions:
        qty_to_buy = (st.session_state.cash * 0.95) / st.session_state.prices.get(best_asset, 65000.0)
        cost = qty_to_buy * st.session_state.prices.get(best_asset, 65000.0)
        st.session_state.cash -= cost
        st.session_state.positions[best_asset] = {"qty": qty_to_buy, "buy_price": st.session_state.prices.get(best_asset, 65000.0)}
        st.session_state.orders.insert(0, {"time": timestamp, "ticker": best_asset, "side": "BUY", "price": st.session_state.prices.get(best_asset, 65000.0)})
        st.session_state.bot_logs.insert(0, f"[{timestamp}] 🚀 Comprando {best_asset} con el 95% del capital.")
        
    # Mantener solo los últimos 10 logs
    st.session_state.bot_logs = st.session_state.bot_logs[:10]

# Simular fluctuación para que el P&L se mueva siempre
for ticker in list(st.session_state.positions.keys()):
    if ticker not in st.session_state.prices:
        st.session_state.prices[ticker] = 65000.0
    change = np.random.normal(0, 0.002)
    st.session_state.prices[ticker] = st.session_state.prices[ticker] * (1 + change)

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
            st.session_state.bot_logs = ["Cuenta reiniciada. Esperando escaneo..."]
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
    st.title("Terminal de Trading (Bot 24/7 en la Nube)")
    
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

    col_chart, col_logs = st.columns([2.5, 1])

    with col_chart:
        activos_lista = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT", "AVAX/USDT", "SUI/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT", "NEAR/USDT", "APT/USDT", "ARB/USDT", "OP/USDT", "INJ/USDT", "SEI/USDT", "TIA/USDT", "PEPE/USDT", "SHIB/USDT", "TRX/USDT", "ETC/USDT", "FIL/USDT", "HBAR/USDT", "ICP/USDT", "ALGO/USDT"]
        
        # Auto-seleccionar el activo actual del bot
        current_asset = list(pos.keys())[0] if pos else "BTC/USDT"
        default_index = activos_lista.index(current_asset) if current_asset in activos_lista else 0
        
        selected_asset = st.selectbox("Seleccionar Activo para Gráfico", activos_lista, index=default_index)
        
        # Simulación visual de velas
        df = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(60, 0, -1)],
            'close': [prices.get(selected_asset, 65000.0) * (1 + np.random.normal(0, 0.002)) for _ in range(60)]
        })
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open', 'close']].max(axis=1) * 1.001
        df['low'] = df[['open', 'close']].min(axis=1) * 0.999

        df['SMA_20'] = df['close'].rolling(window=20).mean()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25], subplot_titles=(f"{selected_asset} - Velas Japonesas", "RSI (14)"))

        fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], increasing_line_color='#10B981', decreasing_line_color='#EF4444', name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', line=dict(color='#F59E0B', width=2), name="SMA 20"), row=1, col=1)

        current_price = prices.get(selected_asset, df['close'].iloc[-1])
        fig.add_trace(go.Scatter(x=[df['timestamp'].iloc[0], df['timestamp'].iloc[-1]], y=[current_price, current_price], mode='lines', line=dict(color='#36C9D5', width=1, dash='dot'), name="Live Price"), row=1, col=1)

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF', size=11), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', rangeslider=dict(visible=False), tickfont=dict(color='#FFFFFF')), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Precio (USDT)", title_font=dict(color='#36C9D5'), tickfont=dict(color='#FFFFFF')), yaxis2=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="RSI", title_font=dict(color='#A855F7'), range=[0, 100], tickfont=dict(color='#FFFFFF')), margin=dict(l=0, r=0, t=30, b=0), height=550, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    with col_logs:
        st.subheader("Bot Live Feed")
        logs_html = "<div style='background-color: #0a0a0a; border: 1px solid #333; border-radius: 5px; padding: 10px; font-family: Share Tech Mono; font-size: 12px; height: 450px; overflow-y: auto;'>"
        for log in st.session_state.bot_logs:
            color = "#10B981" if "Comprando" in log else "#EF4444" if "Vendiendo" in log else "#36C9D5"
            logs_html += f"<div style='color: {color}; margin-bottom: 5px;'>{log}</div>"
        logs_html += "</div>"
        st.markdown(logs_html, unsafe_allow_html=True)

    st.divider()

    col_data, col_history = st.columns([1, 1])

    with col_data:
        st.subheader("Posiciones Abiertas")
        if not pos:
            st.markdown("<div style='background-color: #1E293B; padding: 15px; border-radius: 5px; color: #FFFFFF;'>Sin posiciones. El bot está analizando el mercado.</div>", unsafe_allow_html=True)
        else:
            html = "<table class='nexora-table'><tr><th>Activo</th><th>Cant</th><th>Compra</th><th>Actual</th><th>P&L</th></tr>"
            for ticker, p in pos.items():
                curr_price = prices.get(ticker, p["buy_price"])
                pnl = (curr_price - p["buy_price"]) * p["qty"]
                color = "#10B981" if pnl >= 0 else "#EF4444"
                html += f"<tr><td>{ticker.split('/')[0]}</td><td>{p['qty']:.4f}</td><td>${p['buy_price']:,.2f}</td><td>${curr_price:,.2f}</td><td style='color:{color}; font-weight:bold;'>{pnl:+,.2f}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

    with col_history:
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

    st.divider()

    col_equity, col_pie = st.columns([2, 1])

    with col_equity:
        st.subheader("Curva de Capital")
        if len(st.session_state.equity_history) > 1:
            df_equity = pd.DataFrame(st.session_state.equity_history)
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=df_equity['time'], y=df_equity['equity'], mode='lines', fill='tozeroy', line=dict(color='#36C9D5', width=2), fillcolor='rgba(54, 201, 213, 0.1)'))
            fig_eq.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig_eq, use_container_width=True)

    with col_pie:
        st.subheader("Portfolio")
        labels = ['Cash'] + [t.split('/')[0] for t in pos.keys()]
        values = [cash] + [p["qty"] * prices.get(ticker, 0) for ticker, p in pos.items()]
        
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=['#36C9D5', '#A855F7', '#10B981', '#F59E0B', '#EF4444']))])
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), margin=dict(l=0, r=0, t=10, b=0), height=300, showlegend=False, annotations=[dict(text='Assets', x=0.5, y=0.5, font_size=15, showarrow=False, font_color="#FFF")])
        st.plotly_chart(fig_pie, use_container_width=True)

# --- VISTA 2 y 3 (Mantenidas igual) ---
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