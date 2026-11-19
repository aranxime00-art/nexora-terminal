from enum import StrEnum
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit


class MLModelType(StrEnum):
    LINEAR = "LinearRegression"
    RANDOM_FOREST = "RandomForest"
    XGBOOST = "XGBoost"

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Crea variables predictoras (features) a partir de precios."""
    features = pd.DataFrame(index=df.index)

    # Calcular retornos
    features['ret_1d'] = df['Close'].pct_change(1)
    features['ret_5d'] = df['Close'].pct_change(5)

    # Calcular volatilidad usando los retornos de features
    features['vol_21d'] = features['ret_1d'].rolling(21).std() * np.sqrt(252)

    # RSI simple
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / avg_loss
    features['rsi_14'] = 100 - (100 / (1 + rs))

    return features.dropna()

def train_and_evaluate_model(
    prices: pd.Series,
    model_type: MLModelType = MLModelType.RANDOM_FOREST
) -> dict[str, Any]:
    """Entrena un modelo para predecir el retorno del día siguiente."""
    df = pd.DataFrame({'Close': prices})
    X = create_features(df)

    # Target: Retorno del DÍA SIGUIENTE (shift -1)
    y = df['Close'].pct_change(1).shift(-1).rename("Target")

    # Alinear X e y y eliminar NaNs
    data = pd.concat([X, y], axis=1).dropna()
    X_clean = data.drop(columns=['Target'])
    y_clean = data['Target']

    # Validación Cruzada Temporal
    tscv = TimeSeriesSplit(n_splits=5)

    mse_scores = []
    mae_scores = []

    for train_index, test_index in tscv.split(X_clean):
        X_train, X_test = X_clean.iloc[train_index], X_clean.iloc[test_index]
        y_train, y_test = y_clean.iloc[train_index], y_clean.iloc[test_index]

        if model_type == MLModelType.LINEAR:
            model = LinearRegression()
        elif model_type == MLModelType.RANDOM_FOREST:
            model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        elif model_type == MLModelType.XGBOOST:
            model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)

        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mse_scores.append(mean_squared_error(y_test, preds))
        mae_scores.append(mean_absolute_error(y_test, preds))

    return {
        "model": model_type.value,
        "mean_mse": float(np.mean(mse_scores)),
        "mean_mae": float(np.mean(mae_scores)),
        "num_samples": len(X_clean)
    }
