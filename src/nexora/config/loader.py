from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str
    version: str
    environment: str

class TradingConfig(BaseModel):
    mode: str = Field(pattern="^paper$")
    initial_capital_usd: float
    base_currency: str

class UniverseConfig(BaseModel):
    us_equity: list[str]
    intl_equity: list[str]
    bonds: list[str]
    alternatives: list[str]
    sectors: list[str]

class SystemConfig(BaseModel):
    log_level: str
    timezone: str

class NexoraConfig(BaseModel):
    project: ProjectConfig
    trading: TradingConfig
    universe: UniverseConfig
    system: SystemConfig

def load_config(config_path: Path | str = "config/settings.yaml") -> NexoraConfig:
    """Carga y valida la configuración desde un archivo YAML."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return NexoraConfig(**data)
