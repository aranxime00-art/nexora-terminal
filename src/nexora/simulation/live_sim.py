import ccxt
import time
import pandas as pd
from sqlalchemy.orm import Session
from nexora.data.database import get_engine, init_db, Account, Position, TradeOrder, MarketPrice
from nexora.execution.engine import PaperTradingEngine
from nexora.factors.indicators import calculate_momentum, calculate_rsi
from nexora.utils import setup_logger

class LiveSimulator:
    def __init__(self) -> None:
        self.logger = setup_logger(name="live_sim")
        self.engine = get_engine()
        init_db(self.engine)
        self.trader = PaperTradingEngine(self.engine, commission_rate=0.001, slippage_rate=0.001)
        self.exchange = ccxt.mexc()
        
        # Los 30 activos a monitorear
        self.tickers = [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
            "DOGE/USDT", "DOT/USDT", "LINK/USDT", "TON/USDT", "POL/USDT",
            "AVAX/USDT", "SUI/USDT", "LTC/USDT", "BCH/USDT", "ATOM/USDT",
            "NEAR/USDT", "APT/USDT", "ARB/USDT", "OP/USDT", "INJ/USDT",
            "SEI/USDT", "TIA/USDT", "PEPE/USDT", "SHIB/USDT", "TRX/USDT",
            "ETC/USDT", "FIL/USDT", "HBAR/USDT", "ICP/USDT", "ALGO/USDT"
        ]

    def update_market_prices(self, prices: dict):
        with Session(self.engine) as session:
            for ticker, price in prices.items():
                mp = session.query(MarketPrice).filter_by(ticker=ticker).first()
                if mp:
                    mp.price = price
                else:
                    session.add(MarketPrice(ticker=ticker, price=price))
            session.commit()

    def get_market_data(self) -> tuple:
        prices = {}
        signals = {}
        for symbol in self.tickers:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                prices[symbol] = df['close'].iloc[-1]
                
                # Estrategia: Momentum a 1 mes menos penalización por RSI alto
                mom = calculate_momentum(df['close'])['mom_1m']
                rsi = calculate_rsi(df['close'])
                signals[symbol] = mom - (rsi / 1000) 
            except Exception:
                pass
        return prices, signals

    def execute_cycle(self) -> None:
        print("\n==================================================")
        print("🔍 ESCANEANDO 30 ACTIVOS EN BUSCA DE OPORTUNIDADES...")
        print("==================================================")
        
        prices, signals = self.get_market_data()
        if not prices:
            print("❌ Error de conexión. Reintentando...")
            return
            
        self.update_market_prices(prices)
        
        # Encontrar el mejor activo
        top_ticker = max(signals, key=signals.get)
        top_score = signals[top_ticker]
        
        print(f"💡 El mejor activo detectado es: {top_ticker} (Score: {top_score:.4f})")

        with Session(self.engine) as session:
            acc = session.query(Account).first()
            pos = session.query(Position).first() # Revisar si ya tenemos una posición abierta

            if not acc:
                session.add(Account(cash=50000.0, initial_capital=50000.0))
                session.commit()
                
            # LÓGICA DE VENTA: Si tenemos una posición pero ya no es el mejor activo, la vendemos
            if pos and pos.ticker != top_ticker:
                print(f"🔄 Cambio de oportunidad: Vendiendo {pos.ticker} para comprar {top_ticker}...")
                target_weights = {pos.ticker: 0.0, top_ticker: 0.95}
                self.trader.execute_rebalance(target_weights, prices)
                print(f"✅ Venta de {pos.ticker} ejecutada.")
            
            # LÓGICA DE COMPRA: Si no tenemos nada o acabamos de vender, compramos el nuevo mejor
            elif not pos:
                print(f"🚀 Oportunidad de compra: Adquiriendo {top_ticker}...")
                target_weights = {top_ticker: 0.95}
                self.trader.execute_rebalance(target_weights, prices)
                print(f"✅ Compra de {top_ticker} ejecutada.")
            
            else:
                print(f"⏳ Manteniendo posición actual en {top_ticker}. Esperando mejor oportunidad...")

        print(f"💤 Esperando 10 segundos para el próximo escaneo...")

    def run_forever(self, interval_seconds: int = 10) -> None:
        print("==================================================")
        print("🟢 NEXORA AUTONOMOUS BOT (24/7) INICIADO 🟢")
        print("==================================================")
        while True:
            try:
                self.execute_cycle()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n🛑 Bot detenido.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(interval_seconds)