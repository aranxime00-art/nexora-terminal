from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from nexora.data.database import Account, Position


def get_portfolio_equity(engine: Engine, current_prices: dict[str, float]) -> dict[str, Any]:
    """Calcula el patrimonio total actual."""
    with Session(engine) as session:
        acc = session.query(Account).first()
        if not acc:
            return {"error": "Account not found"}

        positions = session.query(Position).all()
        positions_value = sum(p.quantity * current_prices.get(p.ticker, 0.0) for p in positions)

        return {
            "cash": acc.cash,
            "positions_value": positions_value,
            "total_equity": acc.cash + positions_value,
            "initial_capital": acc.initial_capital,
            "total_return_pct": ((acc.cash + positions_value) / acc.initial_capital - 1.0) * 100
        }

def verify_accounting_integrity(engine: Engine, current_prices: dict[str, float]) -> bool:
    """Verifica que no haya valores negativos o inconsistencias críticas."""
    with Session(engine) as session:
        acc = session.query(Account).first()
        if not acc or acc.cash < 0:
            return False

        positions = session.query(Position).all()
        for p in positions:
            if p.quantity < 0:
                return False
            # Verificar que el precio actual exista para calcular
            if p.ticker not in current_prices:
                return False

    return True
