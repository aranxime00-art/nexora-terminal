import ccxt
import time
import pandas as pd
from sqlalchemy.orm import Session
from nexora.data.database import get_engine, init_db, Account, Position, TradeOrder, MarketPrice
from nexora.execution.mexc_live import MEXCAPIPaperExecutor
from nexora.factors.indicators import calculate_momentum, calculate_rsi
from nexora.utils import setup_logger

class LiveSimulator:
    def __init__(self) -> None:
        self.logger = setup_logger(name="live_sim")
        self.engine = get_engine()
        init_db(self.engine)
        
        # Motor de Paper Trading conectado a la API real para leer saldos
        self.trader = MEXCAPIPaperExecutor()
        
        self.exchange = ccxt.mexc()
        # Lista de activos a analizar
        self.tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
        
        self.sync_balance_with_mexc()

    def sync_balance_with_mexc(self):
        real_cash = self.trader.get_balance('USDT')
        with Session(self.engine) as session:
            acc = session.query(Account).first()
            if not acc:
                # Si no hay cuenta, le inyectamos 50k virtuales si el saldo real es 0
                cap = real_cash if real_cash > 0 else 50000.0
                acc = Account(cash=cap, initial_capital=cap)
                session.add(acc)
            else:
                acc.cash = real_cash if real_cash > 0 else acc.cash
            session.commit()
        self.logger.info(f"🔄 Saldo sincronizado. Capital para Paper Trading: ${acc.cash:.2f} USDT")

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
                # Datos reales desde MEXC
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                prices[symbol] = df['close'].iloc[-1]
                
                # USO DE INDICADORES REALES (Sin aleatoriedad)
                mom = calculate_momentum(df['close'])['mom_1m']
                rsi = calculate_rsi(df['close'])
                
                # Estrategia: Momentum positivo y RSI no sobrecomprado
                if pd.isna(mom) or pd.isna(rsi):
                    signals[symbol] = -999
                else:
                    signals[symbol] = mom - (rsi / 1000) 
            except Exception as e:
                self.logger.error(f"Error obteniendo datos reales de {symbol}: {e}")
        return prices, signals

    def execute_cycle(self) -> None:
        self.logger.info("--- ESCANEANDO MERCADO (DATOS REALES MEXC) ---")
        
        prices, signals = self.get_market_data()
        if not prices:
            self.logger.warning("Sin datos de mercado. Reintentando...")
            return
            
        self.update_market_prices(prices)
        
        # Selección determinista basada en el cálculo del indicador
        top_ticker = max(signals, key=signals.get)
        self.logger.info(f"🏆 Mejor activo por indicadores: {top_ticker} (Score: {signals[top_ticker]:.4f})")

        with Session(self.engine) as session:
            pos = session.query(Position).first()
            acc = session.query(Account).first()
            
            if pos and pos.ticker != top_ticker:
                self.logger.info(f"🔄 Rotando: Vendiendo {pos.ticker}...")
                self.trader.sell(pos.ticker, pos.quantity)
                self.trader.buy(top_ticker, acc.cash * 0.95)
            
            elif not pos:
                if acc.cash > 10:
                    self.logger.info(f"🛒 Oportunidad detectada. Comprando {top_ticker}...")
                    self.trader.buy(top_ticker, acc.cash * 0.95)
            else:
                self.logger.info(f"⏳ Manteniendo {top_ticker}. Esperando mejor oportunidad.")

    def run_forever(self, interval_seconds: int = 60) -> None:
        self.logger.info("🟢 NEXORA BOT INICIADO 🟢")
        while True:
            try:
                self.execute_cycle()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error: {e}")
                time.sleep(interval_seconds)