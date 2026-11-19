import pytest
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from nexora.data.database import Base, Account, TradeOrder
from nexora.data.fetcher import DataFetcher
from nexora.allocation.optimizer import optimize_portfolio, OptimizationMethod
from nexora.execution.engine import PaperTradingEngine

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine

def test_full_pipeline_integration(in_memory_db):
    """Prueba el flujo completo desde la descarga hasta la ejecución de la orden."""
    # 1. Motor de Datos (Simulado con instanciación)
    fetcher = DataFetcher(in_memory_db)
    assert fetcher is not None

    # 2. Motor de Scoring y Asignación
    mock_scores = pd.Series({"SPY": 90.0, "QQQ": 80.0, "GLD": 70.0})
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    np.random.seed(42)
    mock_returns = pd.DataFrame({
        "SPY": np.random.normal(0.0005, 0.01, 100),
        "QQQ": np.random.normal(0.0005, 0.015, 100),
        "GLD": np.random.normal(0.0002, 0.005, 100)
    }, index=dates)
    
    weights = optimize_portfolio(mock_returns, OptimizationMethod.RISK_PARITY)
    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 1e-5

    # 3. Motor de Ejecución (Paper Trading)
    trader = PaperTradingEngine(in_memory_db)
    prices = {"SPY": 400.0, "QQQ": 350.0, "GLD": 180.0}
    
    # Ejecutamos el rebalanceo
    trader.execute_rebalance(weights, prices)
    
    with Session(in_memory_db) as session:
        acc = session.query(Account).first()
        orders = session.query(TradeOrder).all()
        
        # Validar que el flujo terminó en compras
        assert acc.cash < 10000.0
        assert len(orders) > 0
        assert orders[0].side == "BUY"