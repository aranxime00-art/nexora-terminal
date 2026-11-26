# NEXORA — Quantitative Intelligence & Investment System

## Descripción Ejecutiva
NEXORA es un sistema modular de análisis cuantitativo y trading algorítmico desarrollado en Python. El sistema está diseñado para descargar datos de mercado, calcular indicadores técnicos, construir portafolios y ejecutar operaciones simuladas (Paper Trading) en tiempo real sin arriesgar capital real.

## Objetivo General
Proporcionar una plataforma que permita investigar, validar y visualizar estrategias cuantitativas mediante el uso de datos reales de mercado, gestión de riesgos y técnicas de machine learning, operando bajo un entorno seguro de simulación.

## Arquitectura del Sistema
- **Fuente de Datos:** API pública de MEXC mediante la librería CCXT.
- **Motor de Datos:** Almacenamiento local en SQLite (SQLAlchemy).
- **Motor de Factores:** Cálculo de Momentum, RSI, ATR y volatilidad.
- **Paper Trading:** Intercepta las órdenes y las simula localmente, manteniendo la conexión con MEXC para precios reales.
- **Dashboard:** Interfaz en Streamlit desplegada en Streamlit Community Cloud.

## Funcionalidades Implementadas (Reales)
- Conexión autenticada a MEXC mediante API Keys (solo lectura y trading en Paper).
- Descarga y graficación de velas japonesas (OHLCV) reales.
- Cálculo real de indicadores (RSI, SMA).
- Mapa de calor con variaciones porcentuales reales de 24h.
- Cálculo de PnL y métricas de riesgo basadas en historial local.

## Funcionalidades Experimentales / Simuladas
- El bot local utiliza indicadores reales para seleccionar activos, pero la ejecución es 100% simulada.
- Las métricas de riesgo (Sharpe, Drawdown) muestran "N/A" si no hay suficientes datos históricos.
- El módulo de Deep Learning (LSTM) está implementado en el código (`src/nexora/deep_learning/lstm.py`) pero no está conectado al dashboard visual para evitar latencia en la carga.

## Instalación y Ejecución
1. Clonar el repositorio.
2. Crear entorno virtual: `python -m venv .venv`
3. Activar entorno: `.\.venv\Scripts\activate`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Ejecutar bot local: `python -c "from nexora.simulation import LiveSimulator; sim = LiveSimulator(); sim.run_forever(10)"`
6. Ejecutar dashboard local: `streamlit run src/nexora/dashboard/app.py`

## Limitaciones Actuales
- MEXC no provee un entorno Sandbox para Spot a través de su API; por ende, el sistema implementa una simulación local (Paper Trading) conectada a precios reales.
- No se realiza trading con dinero real bajo ninguna circunstancia.

## Advertencia
Este sistema es un proyecto académico y experimental. No constituye asesoría financiera. El trading conlleva riesgos.