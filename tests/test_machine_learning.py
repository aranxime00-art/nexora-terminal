import numpy as np
import pandas as pd
import pytest

from nexora.machine_learning import MLModelType, train_and_evaluate_model


@pytest.fixture
def mock_prices():
    # Generar 500 días de precios sintéticos
    dates = pd.date_range(start="2022-01-01", periods=500, freq="B")
    np.random.seed(42)
    retornos = np.random.normal(0.0005, 0.01, 500)
    precios = 100 * np.exp(np.cumsum(retornos))
    return pd.Series(precios, index=dates)

def test_linear_regression(mock_prices):
    results = train_and_evaluate_model(mock_prices, MLModelType.LINEAR)
    assert results["model"] == "LinearRegression"
    assert results["mean_mse"] >= 0
    assert results["num_samples"] > 0

def test_random_forest(mock_prices):
    results = train_and_evaluate_model(mock_prices, MLModelType.RANDOM_FOREST)
    assert results["model"] == "RandomForest"
    assert results["mean_mse"] >= 0

def test_xgboost(mock_prices):
    results = train_and_evaluate_model(mock_prices, MLModelType.XGBOOST)
    assert results["model"] == "XGBoost"
    assert results["mean_mse"] >= 0
