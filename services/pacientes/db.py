"""Conexion a PostgreSQL. Solo variables de entorno, cero credenciales en el codigo."""
import logging
import os
import time

import psycopg
from psycopg.rows import dict_row

log = logging.getLogger("pacientes")


def get_conn() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        row_factory=dict_row,
        connect_timeout=5,
    )


def wait_for_db(max_attempts: int = 30, delay: float = 2.0) -> bool:
    """Reintenta la conexion al arrancar: en K8s la BD puede tardar mas que el pod."""
    for i in range(1, max_attempts + 1):
        try:
            with get_conn() as conn:
                conn.execute("SELECT 1")
            log.info("Conexion a la BD establecida")
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("BD no disponible (intento %s/%s): %s", i, max_attempts, exc)
            time.sleep(delay)
    log.error("No se pudo conectar a la BD")
    return False