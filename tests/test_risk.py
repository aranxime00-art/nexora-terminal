import numpy as np
import pandas as pd

from nexora.risk import calculate_sharpe_ratio, calculate_sortino_ratio, calculate_var


def test_risk_metrics():
    np.random.seed(42)
    # Generar 252 días de retornos diarios (media 0.05%, vol 1%)
    returns = pd.Series(np.random.normal(0.0005, 0.01, 252))

    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    var = calculate_var(returns)

    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)
    assert isinstance(var, float)

    # El VaR al 95% debe ser negativo
    assert var < 0
