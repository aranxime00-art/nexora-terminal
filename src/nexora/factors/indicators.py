import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_momentum(close: pd.Series) -> Dict[str, float]:
    """Calcula el Momentum a 1, 3, 6, 12 meses y el de 12-1 meses."""
    # Asumiendo 21 días de trading por mes
    m1 = close.pct_change(21).iloc[-1] if len(close) > 21 else np.nan
    m3 = close.pct_change(63).iloc[-1] if len(close) > 63 else np.nan
    m6 = close.pct_change(126).iloc[-1] if len(close) > 126 else np.nan
    m12 = close.pct_change(252).iloc[-1] if len(close) > 252 else np.nan
    
    # Momentum 12 meses excluyendo el último mes (12-1)
    m12_1 = (close.shift(21) / close.shift(252) - 1).iloc[-1] if len(close) > 252 else np.nan
    
    return {"mom_1m": m1, "mom_3m": m3, "mom_6m": m6, "mom_12m": m12, "mom_12_1m": m12_1}

def calculate_rsi(close: pd.Series, period: int = 14) -> float:
    """Calcula el RSI (Relative Strength Index)."""
    if len(close) < period + 1:
        return np.nan
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def calculate_volatility(close: pd.Series, window: int = 21) -> float:
    """Calcula la volatilidad realizada anualizada."""
    if len(close) < window:
        return np.nan
    log_returns: pd.Series = np.log(close / close.shift(1))
    vol = log_returns.rolling(window=window).std() * np.sqrt(252)
    return float(vol.iloc[-1])

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calcula el Average True Range (ATR)."""
    if len(close) < period + 1:
        return np.nan
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, min_periods=period).mean()
    return float(atr.iloc[-1])

def calculate_max_drawdown(close: pd.Series) -> float:
    """Calcula el Maximum Drawdown histórico."""
    if len(close) < 2:
        return np.nan
    roll_max = close.cummax()
    drawdown = close / roll_max - 1.0
    return float(drawdown.min())

def calculate_all_factors(df: pd.DataFrame) -> Dict[str, float]:
    """Recibe un DataFrame con 'High', 'Low', 'Close' y calcula todos los factores."""
    results: Dict[str, Any] = {}
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    # Momentum
    results.update(calculate_momentum(close))
    
    # Reversión a la media
    results['rsi_14'] = calculate_rsi(close)
    
    # Riesgo
    results['volatility_21d'] = calculate_volatility(close)
    results['atr_14'] = calculate_atr(high, low, close)
    results['max_drawdown'] = calculate_max_drawdown(close)
    
    return results