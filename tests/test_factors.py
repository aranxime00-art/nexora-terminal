import pytest
import pandas as pd
import numpy as np
from nexora.factors import calculate_all_factors

@pytest.fixture
def sample_data():
    # Generar 300 días de datos sintéticos
    dates = pd.date_range(start="2023-01-01", periods=300, freq="B")
    np.random.seed(42)
    
    # Simulamos un precio que sube ligeramente con volatilidad
    returns = np.random.normal(0.0005, 0.01, 300)
    close = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'High': close * 1.01,
        'Low': close * 0.99,
        'Close': close
    }, index=dates)
    return df

def test_calculate_all_factors(sample_data):
    factors = calculate_all_factors(sample_data)
    
    # Verificar que existen las llaves
    assert "mom_1m" in factors
    assert "mom_12_1m" in factors
    assert "rsi_14" in factors
    assert "volatility_21d" in factors
    assert "atr_14" in factors
    assert "max_drawdown" in factors
    
    # Verificar que no son todos NaN (ya que hay 300 días)
    assert not np.isnan(factors["mom_12m"])
    assert not np.isnan(factors["rsi_14"])
    assert factors["max_drawdown"] <= 0.0
