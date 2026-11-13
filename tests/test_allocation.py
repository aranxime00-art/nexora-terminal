import pytest
import pandas as pd
import numpy as np
from nexora.allocation import optimize_portfolio, OptimizationMethod

@pytest.fixture
def mock_returns():
    dates = pd.date_range(start="2023-01-01", periods=252, freq="B")
    np.random.seed(42)
    ret_a = np.random.normal(0.0005, 0.005, 252)
    ret_b = np.random.normal(0.0005, 0.010, 252)
    ret_c = np.random.normal(0.0005, 0.020, 252)
    return pd.DataFrame({'A': ret_a, 'B': ret_b, 'C': ret_c}, index=dates)

def test_equal_weight(mock_returns):
    # max_weight=1.0 para que no interfiera con la prueba matemática
    weights = optimize_portfolio(mock_returns, OptimizationMethod.EQUAL_WEIGHT, max_weight=1.0)
    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 1e-5
    assert abs(weights['A'] - 0.3333) < 1e-3

def test_inverse_volatility(mock_returns):
    weights = optimize_portfolio(mock_returns, OptimizationMethod.INVERSE_VOLATILITY, max_weight=1.0)
    assert abs(sum(weights.values()) - 1.0) < 1e-5
    assert weights['A'] > weights['B'] > weights['C']

def test_risk_parity(mock_returns):
    weights = optimize_portfolio(mock_returns, OptimizationMethod.RISK_PARITY, max_weight=1.0)
    assert abs(sum(weights.values()) - 1.0) < 1e-5
    assert weights['A'] > weights['C']

def test_max_weight_constraint(mock_returns):
    # max_weight=0.4 recortará al activo A (que naturalmente pesa ~0.57) y redistribuirá
    weights = optimize_portfolio(mock_returns, OptimizationMethod.INVERSE_VOLATILITY, max_weight=0.4)
    assert abs(sum(weights.values()) - 1.0) < 1e-5
    for w in weights.values():
        assert w <= 0.4 + 1e-5
    assert abs(weights['A'] - 0.4) < 1e-5