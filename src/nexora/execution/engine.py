
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from nexora.data.database import Account, Position, TradeOrder


class PaperTradingEngine:
    def __init__(self, engine: Engine, commission_rate: float = 0.001, slippage_rate: float = 0.0005) -> None:
        self.engine = engine
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

    def get_account(self, session: Session) -> Account:
        """Obtiene la cuenta o la crea con el capital inicial."""
        acc = session.query(Account).first()
        if not acc:
            acc = Account(cash=10000.0, initial_capital=10000.0)
            session.add(acc)
            session.commit()
            session.refresh(acc)
        return acc

    def execute_rebalance(self, target_weights: dict[str, float], current_prices: dict[str, float]) -> None:
        """
        Ejecuta el rebalanceo del portafolio.
        target_weights: Diccionario {ticker: peso_objetivo (0.0 a 1.0)}
        current_prices: Diccionario {ticker: precio_actual}
        """
        with Session(self.engine) as session:
            acc = self.get_account(session)

            # 1. Calcular el valor total actual del portafolio (Cash + Posiciones)
            positions = session.query(Position).all()
            positions_value = sum(p.quantity * current_prices.get(p.ticker, 0.0) for p in positions)
            total_equity = acc.cash + positions_value

            # 2. Calcular objetivos de valor por activo
            target_values = {ticker: weight * total_equity for ticker, weight in target_weights.items()}

            # 3. Calcular diferencias y generar órdenes
            for ticker, target_val in target_values.items():
                price = current_prices.get(ticker)
                if not price or price <= 0:
                    continue

                # Buscar si ya tenemos el activo
                pos = session.query(Position).filter_by(ticker=ticker).first()
                current_qty = pos.quantity if pos else 0.0
                current_val = current_qty * price

                diff_val = target_val - current_val

                # Umbral mínimo para evitar sobre-operar (ej. diferencias menores a $10)
                if abs(diff_val) < 10.0:
                    continue

                # Aplicar Slippage al precio de ejecución
                if diff_val > 0:
                    # COMPRA: Pagamos un poco más por slippage
                    exec_price = price * (1 + self.slippage_rate)
                    qty_to_buy = diff_val / exec_price
                    cost = qty_to_buy * exec_price
                    commission = cost * self.commission_rate

                    if acc.cash >= (cost + commission):
                        acc.cash -= (cost + commission)

                        if pos:
                            # Actualizar precio promedio
                            total_cost = (pos.quantity * pos.average_price) + cost
                            pos.quantity += qty_to_buy
                            pos.average_price = total_cost / pos.quantity
                        else:
                            session.add(Position(ticker=ticker, quantity=qty_to_buy, average_price=exec_price))

                        session.add(TradeOrder(ticker=ticker, side="BUY", quantity=qty_to_buy, price=exec_price, commission=commission, slippage=exec_price-price))

                else:
                    # VENTA: Recibimos un poco menos por slippage
                    exec_price = price * (1 - self.slippage_rate)
                    qty_to_sell = abs(diff_val) / exec_price
                    qty_to_sell = min(qty_to_sell, current_qty) # No vender más de lo que tenemos

                    revenue = qty_to_sell * exec_price
                    commission = revenue * self.commission_rate

                    acc.cash += (revenue - commission)

                    if pos:
                        pos.quantity -= qty_to_sell
                        if pos.quantity <= 1e-6: # Eliminar si queda en 0
                            session.delete(pos)

                    session.add(TradeOrder(ticker=ticker, side="SELL", quantity=qty_to_sell, price=exec_price, commission=commission, slippage=price-exec_price))

            session.commit()
