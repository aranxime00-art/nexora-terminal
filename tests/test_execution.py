import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nexora.data.database import Account, Base, Position, TradeOrder
from nexora.execution import PaperTradingEngine


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

def test_initial_account(in_memory_db):
    trader = PaperTradingEngine(in_memory_db)
    with Session(in_memory_db) as session:
        acc = trader.get_account(session)
        assert acc.cash == 10000.0
        assert acc.initial_capital == 10000.0

def test_execute_buy_order(in_memory_db):
    trader = PaperTradingEngine(in_memory_db)
    prices = {"SPY": 100.0}
    weights = {"SPY": 0.50} # Queremos invertir 50% ($5000) en SPY

    trader.execute_rebalance(weights, prices)

    with Session(in_memory_db) as session:
        acc = session.query(Account).first()
        pos = session.query(Position).first()

        # Verificamos que se gastó el dinero
        assert acc.cash < 5000.0
        # Verificamos que tenemos la posición
        assert pos.ticker == "SPY"
        assert pos.quantity > 0

        # Verificamos la orden
        order = session.query(TradeOrder).first()
        assert order.side == "BUY"
        assert order.ticker == "SPY"

def test_execute_sell_order(in_memory_db):
    trader = PaperTradingEngine(in_memory_db)
    # 1. Compramos primero
    trader.execute_rebalance({"SPY": 1.0}, {"SPY": 100.0})

    # 2. Vendemos todo (weight 0)
    trader.execute_rebalance({"SPY": 0.0}, {"SPY": 100.0})

    with Session(in_memory_db) as session:
        acc = session.query(Account).first()
        pos = session.query(Position).first()

        # El efectivo debería ser casi 10000 (perdimos un poco por comisiones)
        assert acc.cash > 9900.0
        # La posición debe haber sido eliminada
        assert pos is None
