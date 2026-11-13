import numpy as np
import pandas as pd


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calcula el Sharpe Ratio anualizado."""
    if returns.empty or returns.std() == 0:
        return 0.0

    # Asumiendo 252 días de trading
    excess_returns = returns - (risk_free_rate / 252)
    annualized_return = excess_returns.mean() * 252
    annualized_vol = returns.std() * np.sqrt(252)

    return float(annualized_return / annualized_vol)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calcula el Sortino Ratio (solo castiga la volatilidad a la baja)."""
    if returns.empty:
        return 0.0

    excess_returns = returns - (risk_free_rate / 252)
    annualized_return = excess_returns.mean() * 252

    downside_returns = returns[returns < 0]
    if downside_returns.empty or downside_returns.std() == 0:
        return 0.0

    annualized_downside_vol = downside_returns.std() * np.sqrt(252)
    return float(annualized_return / annualized_downside_vol)

def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calcula el Value at Risk diario (ej. 95% de confianza)."""
    if returns.empty:
        return 0.0
    # El VaR es el percentil del 5% para el 95% de confianza
    return float(np.percentile(returns, 100 - (confidence_level * 100)))
