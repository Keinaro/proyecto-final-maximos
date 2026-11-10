import logging
import os
import time

import psycopg
from psycopg.rows import dict_row

log = logging.getLogger("citas")


def _requerida(nombre):
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(f"falta la variable de entorno {nombre}")
    return valor


def parametros():
    return {
        "host": os.environ.get("DB_HOST", "db"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME", "vetdb"),
        "user": _requerida("DB_USER"),
        "password": _requerida("DB_PASSWORD"),
    }


def conectar():
    return psycopg.connect(**parametros(), row_factory=dict_row, connect_timeout=5)


def esperar_base(intentos=30, pausa=2.0):
    # En Kubernetes el pod puede arrancar antes que la base, por eso se reintenta.
    parametros()
    for n in range(1, intentos + 1):
        try:
            with conectar() as conn:
                conn.execute("SELECT 1")
            log.info("conexion con la base establecida")
            return
        except psycopg.OperationalError as exc:
            log.warning("base no disponible, intento %d de %d: %s", n, intentos, str(exc).strip())
            time.sleep(pausa)
    raise RuntimeError("no se pudo conectar con la base de datos")
