import pytest
import pandas as pd
import numpy as np
from nexora.deep_learning import train_lstm_model

@pytest.fixture
def mock_returns():
    np.random.seed(42)
    return pd.Series(np.random.normal(0.0005, 0.01, 100))

def test_lstm_training(mock_returns):
    results = train_lstm_model(mock_returns, seq_length=5, epochs=2)
    
    assert "error" not in results
    assert results["model"] == "LSTM"
    assert results["final_loss"] >= 0.0
    assert results["samples"] > 0