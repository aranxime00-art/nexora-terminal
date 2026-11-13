import pandas as pd
import pytest

from nexora.scoring import calculate_composite_score, rank_assets


@pytest.fixture
def mock_factors():
    # Datos simulados para 3 activos con perfiles distintos
    return pd.DataFrame({
        "mom_12_1m": [0.25, 0.10, -0.05],     # Activo A (ganador), B (neutro), C (perdedor)
        "mom_6m": [0.15, 0.05, -0.02],
        "rsi_14": [70.0, 50.0, 30.0],         # A (sobrecomprado), C (sobrevendido)
        "volatility_21d": [0.15, 0.10, 0.30], # C tiene mucha volatilidad
        "max_drawdown": [-0.10, -0.05, -0.25] # C tiene peor drawdown
    }, index=["A", "B", "C"])

def test_composite_score_calculation(mock_factors):
    scores = calculate_composite_score(mock_factors)

    assert len(scores) == 3
    assert "score" in scores.columns
    assert scores["score"].min() >= 0.0
    assert scores["score"].max() <= 100.0

def test_rank_assets(mock_factors):
    scores = calculate_composite_score(mock_factors)
    ranked = rank_assets(scores)

    # El activo A debería tener mejor score por su momentum
    # El activo C debería tener peor score por su alto riesgo
    assert ranked.index[0] == "A"
    assert ranked.index[-1] == "C"
    assert ranked.loc["A", "score"] > ranked.loc["C", "score"]
