from enum import StrEnum
from typing import cast

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class OptimizationMethod(StrEnum):
    EQUAL_WEIGHT = "EqualWeight"
    INVERSE_VOLATILITY = "InverseVolatility"
    RISK_PARITY = "RiskParity"

def apply_constraints(weights: np.ndarray, max_weight: float = 0.25) -> np.ndarray:
    """Aplica restricciones de peso máximo y asegura que sumen 100%."""
    n = len(weights)
    if max_weight * n < 1.0:
        if weights.sum() == 0:
            return cast(np.ndarray, np.ones(n) / n)
        return cast(np.ndarray, weights / weights.sum())

    w = weights.copy()
    if w.sum() == 0:
        w = np.ones(n) / n
    else:
        w = w / w.sum()

    for _ in range(100):
        over = w > max_weight
        if not np.any(over):
            break
        excess = np.sum(w[over] - max_weight)
        w[over] = max_weight
        under = ~over
        if not np.any(under):
            break
        w[under] += excess / np.sum(under)

    return cast(np.ndarray, w)

def optimize_portfolio(
    returns: pd.DataFrame,
    method: OptimizationMethod = OptimizationMethod.EQUAL_WEIGHT,
    max_weight: float = 0.25
) -> dict[str, float]:
    """Calcula los pesos óptimos para un conjunto de activos."""
    num_assets = len(returns.columns)
    if num_assets == 0:
        return {}

    if method == OptimizationMethod.EQUAL_WEIGHT:
        weights = np.ones(num_assets) / num_assets
        weights = apply_constraints(weights, max_weight)

    elif method == OptimizationMethod.INVERSE_VOLATILITY:
        vols = returns.std() * np.sqrt(252)
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        weights_arr = cast(np.ndarray, weights.to_numpy())
        weights = apply_constraints(weights_arr, max_weight)

    elif method == OptimizationMethod.RISK_PARITY:
        cov_matrix = returns.cov() * 252
        cov_np = cov_matrix.values

        # Formulación logarítmica de Spinu (2013) para máxima estabilidad
        def objective(w: np.ndarray) -> float:
            port_var = float(w.T @ cov_np @ w)
            epsilon = 1e-8  # Para evitar log(0)
            log_term = -np.sum(np.log(np.maximum(w, epsilon))) / num_assets
            return float(0.5 * port_var + log_term)

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        bounds = tuple((1e-8, max_weight) for _ in range(num_assets))
        initial_guess = np.ones(num_assets) / num_assets

        try:
            result = minimize(
                objective, initial_guess, method='SLSQP',
                bounds=bounds, constraints=constraints
            )
            weights = result.x if result.success else initial_guess
        except Exception:
            weights = initial_guess

        weights = apply_constraints(weights, max_weight)

    return {ticker: float(w) for ticker, w in zip(returns.columns, weights)}
