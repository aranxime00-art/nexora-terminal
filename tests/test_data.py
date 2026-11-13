import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nexora.data.database import Asset, Base, PriceHistory
from nexora.data.fetcher import DataFetcher


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

def test_create_asset(in_memory_db):
    with Session(in_memory_db) as session:
        fetcher = DataFetcher(in_memory_db)
        asset = fetcher.get_or_create_asset(session, "SPY", "US_EQUITY")
        assert asset.id is not None
        assert asset.ticker == "SPY"
        assert asset.asset_class == "US_EQUITY"

        # Probamos que no duplique
        asset2 = fetcher.get_or_create_asset(session, "SPY", "US_EQUITY")
        assert asset.id == asset2.id

def test_price_history_relationship(in_memory_db):
    with Session(in_memory_db) as session:
        asset = Asset(ticker="QQQ", asset_class="US_EQUITY")
        session.add(asset)
        session.commit()

        price = PriceHistory(
            asset_id=asset.id,
            date=__import__('datetime').date(2024, 1, 1),
            close=400.0,
            adj_close=400.0
        )
        session.add(price)
        session.commit()

        assert price.id is not None
        assert price.asset_id == asset.id
