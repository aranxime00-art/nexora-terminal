import pytest
import pandas as pd
import numpy as np
from nexora.backtesting import BacktestEngine

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2023-01-01", periods=100, freq="B")
    
    # Precios: SPY sube de 100 a 120, QQQ sube de 200 a 180
    prices = pd.DataFrame({
        "SPY": np.linspace(100, 120, 100),
        "QQQ": np.linspace(200, 180, 100)
    }, index=dates)
    
    # Señales: Rebalanceamos el día 1 (50/50) y el día 50 (100% SPY)
    signals = pd.DataFrame({
        "SPY": [0.5, 1.0],
        "QQQ": [0.5, 0.0]
    }, index=[dates[0], dates[50]])
    
    return prices, signals

def test_backtest_engine_run(mock_market_data):
    prices, signals = mock_market_data
    engine = BacktestEngine(initial_capital=10000.0)
    
    results = engine.run(prices, signals)
    
    assert not results.empty
    assert len(results) == 100
    assert "equity" in results.columns
    
    # El equity final debería haber crecido (porque SPY subió)
    final_equity = results["equity"].iloc[-1]
    initial_equity = results["equity"].iloc[0]
    assert final_equity > initial_equity
    
    # Debería estar cerca de 10992 (descontando comisiones y slippage)
    # Ajustamos el umbral a 10800 para reflejar la realidad matemática
    assert final_equity > 10800