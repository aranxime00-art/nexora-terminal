import numpy as np
import pandas as pd

from nexora.regimes import MarketRegime, detect_market_regime


def generate_series(trend: str, periods: int = 300) -> pd.DataFrame:
    """Genera datos sintéticos para simular diferentes mercados."""
    dates = pd.date_range(start="2023-01-01", periods=periods, freq="B")
    np.random.seed(42)

    if trend == "expansion":
        # Sube constantemente
        close = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.005, periods)))
    elif trend == "stress":
        # Cae fuerte y con alta volatilidad
        close = 100 * np.exp(np.cumsum(np.random.normal(-0.002, 0.02, periods)))
    elif trend == "recovery":
        # Caída del 20% y rebote parcial del 5% (simula una recuperación real)
        drop = np.linspace(100, 80, 150)
        rebound = np.linspace(80, 84, 150)
        full_close = np.concatenate([drop, rebound])
        close = full_close[:periods]

    return pd.DataFrame({'Close': close}, index=dates)

def test_expansion_regime():
    df = generate_series("expansion")
    regime = detect_market_regime(df)
    assert regime == MarketRegime.EXPANSION

def test_stress_regime():
    df = generate_series("stress")
    regime = detect_market_regime(df)
    assert regime == MarketRegime.STRESS

def test_recovery_regime():
    df = generate_series("recovery")
    regime = detect_market_regime(df)
    assert regime == MarketRegime.RECOVERY

def test_insufficient_data():
    df = generate_series("expansion", periods=100)
    regime = detect_market_regime(df)
    assert regime == MarketRegime.UNCERTAINTY
