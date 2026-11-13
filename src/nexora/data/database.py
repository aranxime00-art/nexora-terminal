from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import Engine
from pathlib import Path
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    asset_class = Column(String, nullable=False)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('asset_id', 'date', name='uix_asset_date'),
    )

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    cash = Column(Float, nullable=False, default=10000.0)
    initial_capital = Column(Float, nullable=False, default=10000.0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, unique=True, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)

class TradeOrder(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False) # "BUY" or "SELL"
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)
    slippage = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def get_engine(db_path: str = "data/nexora.db") -> Engine:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")

def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)