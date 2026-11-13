import sys
from pathlib import Path

from nexora.config import load_config
from nexora.utils import setup_logger


def main() -> None:
    """Punto de entrada principal de verificación de NEXORA."""
    print("Iniciando NEXORA - Quantitative Intelligence & Investment System...")

    if sys.version_info[:2] != (3, 12):
        print(f"ADVERTENCIA: Se requiere Python 3.12. Versión actual: {sys.version}")
        sys.exit(1)

    try:
        # Buscar configuración en la raíz del proyecto
        root_dir = Path(__file__).resolve().parent.parent.parent
        config_path = root_dir / "config" / "settings.yaml"

        config = load_config(config_path)

        # Configurar logger
        logger = setup_logger(log_level=config.system.log_level, log_dir=str(root_dir / "logs"))

        logger.info(f"Entorno: {config.project.environment}")
        logger.info(f"Modo de trading: {config.trading.mode.upper()}")
        capital = config.trading.initial_capital_usd
        currency = config.trading.base_currency
        logger.info(f"Capital inicial virtual: {capital} {currency}")
        logger.info(
            f"Universo cargado con {len(config.universe.us_equity)} activos de renta variable US."
        )
        logger.info("Verificación de Fase 1 completada exitosamente.")

    except Exception as e:
        print(f"ERROR CRÍTICO AL INICIAR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
