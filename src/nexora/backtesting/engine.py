from typing import Any

import pandas as pd


class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0, commission_rate: float = 0.001, slippage_rate: float = 0.0005) -> None:
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        self.cash = initial_capital
        self.positions: dict[str, float] = {} # {ticker: quantity}
        self.history: list[dict[str, Any]] = []

    def _execute_trades(self, target_weights: dict[str, float], current_prices: dict[str, float]) -> None:
        """Ejecuta el rebalanceo en el simulador."""
        total_equity = self.cash + sum(qty * current_prices.get(ticker, 0.0) for ticker, qty in self.positions.items())

        for ticker, weight in target_weights.items():
            price = current_prices.get(ticker)
            if not price or price <= 0:
                continue

            target_val = weight * total_equity
            current_qty = self.positions.get(ticker, 0.0)
            current_val = current_qty * price
            diff_val = target_val - current_val

            # Umbral mínimo de $10 para evitar sobre-operar
            if abs(diff_val) < 10.0:
                continue

            if diff_val > 0:
                # Compra
                exec_price = price * (1 + self.slippage_rate)
                qty_to_buy = diff_val / exec_price
                cost = qty_to_buy * exec_price
                commission = cost * self.commission_rate

                if self.cash >= (cost + commission):
                    self.cash -= (cost + commission)
                    self.positions[ticker] = self.positions.get(ticker, 0.0) + qty_to_buy
            else:
                # Venta
                exec_price = price * (1 - self.slippage_rate)
                qty_to_sell = min(abs(diff_val) / exec_price, current_qty)

                if qty_to_sell > 0:
                    revenue = qty_to_sell * exec_price
                    commission = revenue * self.commission_rate
                    self.cash += (revenue - commission)
                    self.positions[ticker] -= qty_to_sell
                    if self.positions[ticker] <= 1e-6:
                        del self.positions[ticker]

    def run(self, prices_df: pd.DataFrame, weight_signals: pd.DataFrame) -> pd.DataFrame:
        """
        Corre el backtest.
        prices_df: DataFrame con precios de cierre (index=dates, columns=tickers)
        weight_signals: DataFrame con los pesos objetivo (index=rebalance_dates, columns=tickers)
        """
        # Asegurar que las fechas estén ordenadas
        prices_df = prices_df.sort_index()
        weight_signals = weight_signals.sort_index()

        for current_date, row in prices_df.iterrows():
            # Actualizar precios actuales
            current_prices = {ticker: row[ticker] for ticker in prices_df.columns if not pd.isna(row[ticker])}

            # Verificar si hoy toca rebalanceo
            if current_date in weight_signals.index:
                target_weights = weight_signals.loc[current_date].dropna().to_dict()
                self._execute_trades(target_weights, current_prices)

            # Registrar el valor del portafolio
            positions_val = sum(qty * current_prices.get(ticker, 0.0) for ticker, qty in self.positions.items())
            total_equity = self.cash + positions_val

            self.history.append({
                "date": current_date,
                "equity": total_equity,
                "cash": self.cash
            })

        return pd.DataFrame(self.history).set_index("date")
