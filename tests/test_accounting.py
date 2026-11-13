import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nexora.data.database import Account, Base, Position
from nexora.portfolio import get_portfolio_equity, verify_accounting_integrity


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

def test_portfolio_equity(in_memory_db):
    with Session(in_memory_db) as session:
        session.add(Account(cash=5000.0, initial_capital=10000.0))
        session.add(Position(ticker="SPY", quantity=50.0, average_price=100.0))
        session.commit()

    prices = {"SPY": 110.0} # 50 * 110 = 5500
    equity = get_portfolio_equity(in_memory_db, prices)

    assert equity["cash"] == 5000.0
    assert equity["positions_value"] == 5500.0
    assert equity["total_equity"] == 10500.0
    assert abs(equity["total_return_pct"] - 5.0) < 1e-5

def test_accounting_integrity(in_memory_db):
    with Session(in_memory_db) as session:
        session.add(Account(cash=5000.0, initial_capital=10000.0))
        session.commit()

    assert verify_accounting_integrity(in_memory_db, {}) == True

def test_accounting_fails_with_negative_cash(in_memory_db):
    with Session(in_memory_db) as session:
        session.add(Account(cash=-100.0, initial_capital=10000.0))
        session.commit()

    # Debería fallar por tener efectivo negativo
    assert verify_accounting_integrity(in_memory_db, {}) == False
