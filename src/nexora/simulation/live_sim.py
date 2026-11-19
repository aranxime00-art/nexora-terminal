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
        # Lista ampliada a 30 activos
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
                print(f"   [API] Consultando {symbol}...")
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                prices[symbol] = df['close'].iloc[-1]
                mom = calculate_momentum(df['close'])['mom_1m']
                rsi = calculate_rsi(df['close'])
                signals[symbol] = mom - (rsi / 1000)
            except Exception as e:
                print(f"   [ERROR] No se pudo obtener {symbol}: {e}")
        return prices, signals

    def execute_cycle(self) -> None:
        print("\n==================================================")
        print("--- INICIANDO CICLO DE ANÁLISIS CUANTITATIVO (30 ACTIVOS) ---")
        print("==================================================")
        
        prices, signals = self.get_market_data()
        if not prices:
            print("❌ No se obtuvieron datos. Reintentando...")
            return
            
        self.update_market_prices(prices)
            
        top_ticker = max(signals, key=signals.get)
        print(f"✅ Mejor activo: {top_ticker} (Score: {signals[top_ticker]:.4f})")

        with Session(self.engine) as session:
            acc = session.query(Account).first()
            if not acc:
                session.add(Account(cash=50000.0, initial_capital=50000.0))
                session.commit()

        target_weights = {top_ticker: 0.95}
        self.trader.execute_rebalance(target_weights, prices)
        print(f"🚀 Rebalanceo ejecutado. Portafolio asignado a {top_ticker}.")
        print(f"⏳ Esperando para el siguiente análisis...\n")

    def run_forever(self, interval_seconds: int = 2) -> None:
        print("==================================================")
        print("🟢 NEXORA AUTONOMOUS BOT INICIADO (MEXC LIVE - 30 ACTIVOS) 🟢")
        print("==================================================")
        while True:
            try:
                self.execute_cycle()
                for i in range(interval_seconds):
                    time.sleep(1)
                    print(f"   [SISTEMA VIVO] Próximo análisis en {interval_seconds - i} segundos...", end="\r")
                print(" " * 60, end="\r")
            except KeyboardInterrupt:
                print("\n🛑 Simulador detenido.")
                break
            except Exception as e:
                print(f"\n❌ Error en el ciclo: {e}")
                time.sleep(interval_seconds)