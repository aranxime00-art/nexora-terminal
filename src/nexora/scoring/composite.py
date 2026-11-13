
import pandas as pd

# Pesos por defecto según especificación
WEIGHTS = {
    "momentum": 0.35,
    "mean_reversion": 0.20,
    "risk": 0.25,
    "relative_strength": 0.20
}

def z_score_normalize(series: pd.Series) -> pd.Series:
    """Normaliza una serie usando Z-Score, manejando valores extremos y nulos."""
    series = series.fillna(series.mean())
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(0.0, index=series.index)

    z = (series - mean) / std
    return z.clip(-3, 3)

def calculate_composite_score(factors_df: pd.DataFrame) -> pd.DataFrame:
    """Recibe un DataFrame con los factores de múltiples activos."""
    df = factors_df.copy()

    # 1. Normalización de Momentum
    df["z_momentum"] = z_score_normalize(df["mom_12_1m"])

    # 2. Normalización de Reversión (invertida)
    df["z_reversion"] = -z_score_normalize(df["rsi_14"])

    # 3. Normalización de Riesgo (invertido)
    df["z_risk"] = -z_score_normalize(df["volatility_21d"]) - z_score_normalize(df["max_drawdown"])

    # 4. Normalización de Fuerza Relativa
    # Proxy inicial: momentum 6m. En Fase 5 se compara vs SPY.
    df["z_strength"] = z_score_normalize(df["mom_6m"])

    # 5. Calcular el Score Ponderado
    raw_score = (
        df["z_momentum"] * WEIGHTS["momentum"] +
        df["z_reversion"] * WEIGHTS["mean_reversion"] +
        df["z_risk"] * WEIGHTS["risk"] +
        df["z_strength"] * WEIGHTS["relative_strength"]
    )

    # 6. Escalar de -3..3 a 0..100
    min_raw = raw_score.min()
    max_raw = raw_score.max()

    if max_raw == min_raw:
        df["score"] = 50.0
    else:
        df["score"] = ((raw_score - min_raw) / (max_raw - min_raw)) * 100.0

    return df[["score", "z_momentum", "z_reversion", "z_risk", "z_strength"]]

def rank_assets(scores_df: pd.DataFrame) -> pd.DataFrame:
    """Ordena los activos de mayor a menor score."""
    return scores_df.sort_values(by="score", ascending=False)
