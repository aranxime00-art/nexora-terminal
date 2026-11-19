from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from nexora.data.database import get_engine, init_db
from nexora.utils.logging import setup_logger


class NexoraScheduler:
    def __init__(self) -> None:
        self.engine = get_engine()
        init_db(self.engine)
        self.logger = setup_logger(name="nexora_scheduler")
        self.scheduler = BlockingScheduler()

    def daily_routine(self) -> None:
        """Rutina principal que se ejecutará diariamente."""
        self.logger.info("--- INICIANDO RUTINA DIARIA DE NEXORA ---")

        # Aquí en el futuro se conectarán los módulos de descarga y cálculo
        # Ejemplo:
        # fetcher = DataFetcher(self.engine)
        # fetcher.fetch_and_store(...)

        self.logger.info("Descarga de datos: [Simulado - OK]")
        self.logger.info("Cálculo de factores: [Simulado - OK]")
        self.logger.info("Ejecución de órdenes: [Simulado - OK]")

        self.logger.info(f"Rutina completada a las {datetime.now()}")
        self.logger.info("-----------------------------------------")

    def start(self) -> None:
        """Inicia el programador en primer plano (mantiene el proceso vivo)."""
        self.logger.info("Iniciando Orquestador NEXORA 24/7...")
        self.logger.info("Presiona Ctrl+C para detener el servicio.")

        # Programar la tarea: de Lunes a Viernes a las 18:00 (6 PM, cierre de mercado NY)
        self.scheduler.add_job(
            self.daily_routine,
            'cron',
            day_of_week='mon-fri',
            hour=18,
            minute=0
        )

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Orquestador detenido manualmente.")
