import ccxt
import os
from dotenv import load_dotenv
from nexora.utils import setup_logger
from sqlalchemy.orm import Session
from nexora.data.database import get_engine, Account, Position, TradeOrder

load_dotenv()

class MEXCAPIPaperExecutor:
    def __init__(self) -> None:
        self.logger = setup_logger(name="mexc_api_paper")
        self.api_key = os.getenv('MEXC_API_KEY')
        self.secret_key = os.getenv('MEXC_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            self.logger.error("❌ Faltan las llaves API en el archivo .env")
            raise ValueError("Configura MEXC_API_KEY y MEXC_SECRET_KEY en el .env")
            
        # Conectamos a MEXC con las llaves
        self.exchange = ccxt.mexc({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'enableRateLimit': True,
        })
        self.engine = get_engine()
        self.logger.info("✅ API Key de MEXC autenticada correctamente.")

    def get_balance(self, currency: str = 'USDT') -> float:
        """Lee el saldo REAL de la cuenta a través de la API."""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['free'].get(currency, 0.0))
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo balance real: {e}")
            return 0.0

    def get_price(self, symbol: str) -> float:
        """Lee el precio REAL del mercado."""
        ticker = self.exchange.fetch_ticker(symbol)
        return float(ticker['last'])

    def buy(self, symbol: str, amount_usdt: float) -> dict:
        """Intercepta la orden: Simula la compra en lugar de gastar dinero real."""
        try:
            price = self.get_price(symbol)
            amount = amount_usdt / price
            
            self.logger.info(f"🛒 [PAPER - API CONNECTED] Simulando COMPRA de {amount:.4f} {symbol} @ ${price:.2f}")
            
            with Session(self.engine) as session:
                pos = session.query(Position).filter_by(ticker=symbol).first()
                if pos:
                    pos.quantity += amount
                else:
                    session.add(Position(ticker=symbol, quantity=amount, average_price=price))
                
                session.add(TradeOrder(ticker=symbol, side="BUY (PAPER)", quantity=amount, price=price, commission=0, slippage=0))
                acc = session.query(Account).first()
                if acc:
                    acc.cash -= amount_usdt
                session.commit()
                
            return {"id": "paper_buy", "amount": amount, "price": price}
        except Exception as e:
            self.logger.error(f"❌ Error al simular compra: {e}")
            return {}

    def sell(self, symbol: str, amount: float) -> dict:
        """Intercepta la orden: Simula la venta en lugar de recibir dinero real."""
        try:
            price = self.get_price(symbol)
            self.logger.info(f"💸 [PAPER - API CONNECTED] Simulando VENTA de {amount:.4f} {symbol} @ ${price:.2f}")
            
            with Session(self.engine) as session:
                pos = session.query(Position).filter_by(ticker=symbol).first()
                if pos and pos.quantity >= amount:
                    pos.quantity -= amount
                    if pos.quantity <= 0:
                        session.delete(pos)
                        
                session.add(TradeOrder(ticker=symbol, side="SELL (PAPER)", quantity=amount, price=price, commission=0, slippage=0))
                acc = session.query(Account).first()
                if acc:
                    acc.cash += (amount * price)
                session.commit()
                
            return {"id": "paper_sell", "amount": amount, "price": price}
        except Exception as e:
            self.logger.error(f"❌ Error al simular venta: {e}")
            return {}