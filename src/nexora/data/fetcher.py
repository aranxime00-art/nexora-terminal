import pandas as pd
import yfinance as yf  # type: ignore
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from nexora.data.database import Asset, PriceHistory


class DataFetcher:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_or_create_asset(self, session: Session, ticker: str, asset_class: str) -> Asset:
        asset = session.query(Asset).filter_by(ticker=ticker).first()
        if not asset:
            asset = Asset(ticker=ticker, asset_class=asset_class, name=ticker)
            session.add(asset)
            session.commit()
            session.refresh(asset)
        return asset
    def fetch_and_store(
        self, tickers: list[str], asset_class: str, start_date: str = "2020-01-01"
    ) -> None:
        """Descarga datos de Yahoo Finance y los guarda en SQLite de forma segura."""
        print(f"Descargando datos para: {tickers}")

        # Descarga en bloque
        data = yf.download(
            tickers, start=start_date, group_by='ticker', auto_adjust=False, progress=False
        )

        for ticker in tickers:
            print(f"Procesando {ticker}...")

            # Extraer datos del ticker
            try:
                df = data if len(tickers) == 1 else data[ticker]
            except KeyError:
                print(f"Advertencia: No se encontraron datos para {ticker}")
                continue

            if df.empty:
                print(f"Advertencia: DataFrame vacío para {ticker}")
                continue

            # Limpieza básica
            df = df.dropna(subset=['Close'])

            # Abrimos una sesión limpia por cada ticker para evitar bloqueos
            with Session(self.engine) as session:
                asset = self.get_or_create_asset(session, ticker, asset_class)

                records = []
                for idx, row in df.iterrows():
                    exists = session.query(PriceHistory).filter_by(
                        asset_id=asset.id,
                        date=idx.date()
                    ).first()

                    if not exists:
                        adj_close_val = row['Adj Close'] if 'Adj Close' in row else row['Close']
                        records.append(PriceHistory(
                            asset_id=asset.id,
                            date=idx.date(),
                            open=float(row['Open']) if pd.notna(row['Open']) else None,
                            high=float(row['High']) if pd.notna(row['High']) else None,
                            low=float(row['Low']) if pd.notna(row['Low']) else None,
                            close=float(row['Close']),
                            adj_close=(
                                float(adj_close_val)
                                if pd.notna(adj_close_val)
                                else float(row['Close'])
                            ),
                            volume=int(row['Volume']) if pd.notna(row['Volume']) else None
                        ))

                if records:
                    session.add_all(records)
                    session.commit()
                    print(f"Guardados {len(records)} registros para {ticker}.")
                else:
                    print(f"No hay registros nuevos para {ticker}.")
