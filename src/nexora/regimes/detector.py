import pandas as pd
import numpy as np
from enum import StrEnum
from typing import cast

class MarketRegime(StrEnum):
    EXPANSION = "Expansion"
    UNCERTAINTY = "Uncertainty"
    STRESS = "Stress"
    RECOVERY = "Recovery"

def detect_market_regime(spy_df: pd.DataFrame) -> MarketRegime:
    """
    Detecta el régimen actual del mercado basado en el SPY.
    Requiere un DataFrame con la columna 'Close'.
    """
    if len(spy_df) < 252:
        return MarketRegime.UNCERTAINTY  # Datos insuficientes

    close = spy_df['Close']
    current_price = close.iloc[-1]
    
    # 1. Tendencia (SMA 200)
    sma_200 = close.rolling(window=200).mean().iloc[-1]
    is_uptrend = current_price > sma_200
    
    # 2. Drawdown desde el máximo de 252 días (1 año)
    rolling_max = close.rolling(window=252, min_periods=1).max().iloc[-1]
    drawdown = (current_price / rolling_max) - 1.0
    
    # 3. Volatilidad realizada anualizada (21 días)
    log_returns = cast(pd.Series, np.log(close / close.shift(1)))
    volatility = log_returns.rolling(window=21).std().iloc[-1] * np.sqrt(252)

    # --- Lógica de Clasificación ---
    
    # Estrés: Caída mayor al 15% o volatilidad extrema (> 40%)
    if drawdown < -0.15 or volatility > 0.40:
        return MarketRegime.STRESS
        
    # Recuperación: Viene de una caída (>10%) pero está intentando subir (sobre SMA50)
    sma_50 = close.rolling(window=50).mean().iloc[-1]
    if drawdown < -0.10 and current_price > sma_50:
        return MarketRegime.RECOVERY
        
    # Expansión: Tendencia alcista clara y cerca de máximos
    if is_uptrend and drawdown > -0.05:
        return MarketRegime.EXPANSION
        
    # Cualquier otro caso es Incertidumbre
    return MarketRegime.UNCERTAINTY