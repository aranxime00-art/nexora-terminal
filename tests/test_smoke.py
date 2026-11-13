import sys
from pathlib import Path

from nexora.config import NexoraConfig, load_config
from nexora.utils import setup_logger


def test_python_version():
    """Verifica que se esté ejecutando en Python 3.12."""
    assert sys.version_info[:2] == (3, 12), "Las pruebas deben ejecutarse en Python 3.12"

def test_config_loads(root_path: Path):
    """Verifica que el archivo YAML se cargue y valide correctamente."""
    config_path = root_path / "config" / "settings.yaml"
    config = load_config(config_path)

    assert isinstance(config, NexoraConfig)
    assert config.trading.mode == "paper"
    assert config.trading.initial_capital_usd == 10000.0
    assert "SPY" in config.universe.us_equity

def test_logger_setup(tmp_path: Path):
    """Verifica que el logger cree el archivo de log correctamente."""
    logger = setup_logger(log_dir=str(tmp_path))
    logger.info("Test de logging")

    log_file = tmp_path / "nexora.log"
    assert log_file.exists()
    assert "Test de logging" in log_file.read_text(encoding="utf-8")
