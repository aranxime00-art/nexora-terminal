import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "nexora", log_level: str = "INFO", log_dir: str = "logs"
) -> logging.Logger:
    """Configura un logger estructurado que escribe en consola y archivo."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Evitar duplicados si se llama múltiples veces
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Archivo
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path / "nexora.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
