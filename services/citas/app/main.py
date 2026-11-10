import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import psycopg
from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import errors
from starlette.exceptions import HTTPException as HttpError

from . import db
from .schemas import CitaCambios, CitaNueva, traducir_error

log = logging.getLogger("citas")

VERSION = os.environ.get("APP_VERSION", "1.0.0")
COLUMNAS = "id, paciente_id, fecha_hora, motivo, veterinario, estado"


class ErrorApi(Exception):
    def __init__(self, status, mensaje):
        self.status = status
        self.mensaje = mensaje


@asynccontextmanager
async def ciclo_de_vida(_app):
    log.info("citas %s iniciando", VERSION)
    db.esperar_base()
    yield


app = FastAPI(title="Citas", version=VERSION, lifespan=ciclo_de_vida)


def error_json(status, mensaje):
    return JSONResponse(status_code=status, content={"error": mensaje})


@app.exception_handler(ErrorApi)
async def _error_api(_request: Request, exc: ErrorApi):
    return error_json(exc.status, exc.mensaje)


@app.exception_handler(RequestValidationError)
async def _validacion(_request: Request, exc: RequestValidationError):
    return error_json(400, traducir_error(exc.errors()[0]))


@app.exception_handler(HttpError)
async def _http(_request: Request, exc: HttpError):
    textos = {404: "no encontrado", 405: "metodo no permitido"}
    return error_json(exc.status_code, textos.get(exc.status_code, str(exc.detail)))


@app.exception_handler(psycopg.OperationalError)
async def _sin_base(_request: Request, exc: psycopg.OperationalError):
    log.error("base de datos no disponible: %s", str(exc).strip())
    return error_json(503, "base de datos no disponible")


@app.exception_handler(Exception)
async def _inesperado(_request: Request, exc: Exception):
    log.exception("error no controlado", exc_info=exc)
    return error_json(500, "error interno")


def serializar(fila):
    fila = dict(fila)
    fila["fecha_hora"] = fila["fecha_hora"].isoformat()
    return fila


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/citas")
def listar(paciente_id: Optional[int] = Query(default=None)):
    sql = f"SELECT {COLUMNAS} FROM citas"
    parametros = []
    if paciente_id is not None:
        sql += " WHERE paciente_id = %s"
        parametros.append(paciente_id)
    sql += " ORDER BY fecha_hora, id"
    with db.conectar() as conn:
        filas = conn.execute(sql, parametros).fetchall()
    return [serializar(f) for f in filas]


@app.get("/citas/{cita_id}")
def obtener(cita_id: int):
    with db.conectar() as conn:
        fila = conn.execute(f"SELECT {COLUMNAS} FROM citas WHERE id = %s", (cita_id,)).fetchone()
    if fila is None:
        raise ErrorApi(404, "cita no encontrada")
    return serializar(fila)


@app.post("/citas", status_code=201)
def crear(datos: CitaNueva):
    try:
        with db.conectar() as conn:
            fila = conn.execute(
                "INSERT INTO citas (paciente_id, fecha_hora, motivo, veterinario, estado) "
                "VALUES (%(paciente_id)s, %(fecha_hora)s, %(motivo)s, %(veterinario)s, %(estado)s) "
                f"RETURNING {COLUMNAS}",
                datos.model_dump(),
            ).fetchone()
    except errors.ForeignKeyViolation:
        raise ErrorApi(400, "paciente no existe")
    return serializar(fila)


@app.put("/citas/{cita_id}")
def actualizar(cita_id: int, datos: CitaCambios):
    cambios = datos.model_dump(exclude_unset=True)
    try:
        with db.conectar() as conn:
            if cambios:
                asignaciones = ", ".join(f"{campo} = %({campo})s" for campo in cambios)
                fila = conn.execute(
                    f"UPDATE citas SET {asignaciones} WHERE id = %(id)s RETURNING {COLUMNAS}",
                    {**cambios, "id": cita_id},
                ).fetchone()
            else:
                fila = conn.execute(
                    f"SELECT {COLUMNAS} FROM citas WHERE id = %s", (cita_id,)
                ).fetchone()
    except errors.ForeignKeyViolation:
        raise ErrorApi(400, "paciente no existe")
    if fila is None:
        raise ErrorApi(404, "cita no encontrada")
    return serializar(fila)


@app.delete("/citas/{cita_id}", status_code=204)
def eliminar(cita_id: int):
    with db.conectar() as conn:
        borradas = conn.execute("DELETE FROM citas WHERE id = %s", (cita_id,)).rowcount
    if borradas == 0:
        raise ErrorApi(404, "cita no encontrada")
    return Response(status_code=204)
