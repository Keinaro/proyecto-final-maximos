import logging
import os
import threading
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from db import get_conn, wait_for_db
from schemas import PacienteIn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pacientes")

APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")

COLUMNAS = (
    "id, nombre, especie, raza, fecha_nacimiento, "
    "propietario_nombre, propietario_telefono"
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # La espera de la BD corre en segundo plano para que /health responda desde el inicio
    threading.Thread(target=wait_for_db, daemon=True).start()
    yield


app = FastAPI(title="Pacientes", version=APP_VERSION, lifespan=lifespan)


def error(status: int, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": mensaje})


# ---- Errores con el formato del contrato: {"error": "mensaje"} ----
@app.exception_handler(RequestValidationError)
async def validation_handler(_req: Request, exc: RequestValidationError):
    primero = exc.errors()[0]
    campo = ".".join(str(p) for p in primero["loc"] if p != "body")
    return error(400, f"{campo}: {primero['msg']}" if campo else primero["msg"])


@app.exception_handler(StarletteHTTPException)
async def http_handler(_req: Request, exc: StarletteHTTPException):
    mensaje = "ruta no encontrada" if exc.status_code == 404 and exc.detail == "Not Found" else str(exc.detail)
    return error(exc.status_code, mensaje)


@app.exception_handler(Exception)
async def generic_handler(_req: Request, exc: Exception):
    log.exception("Error no controlado: %s", exc)
    return error(500, "error interno del servidor")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    log.info("%s %s", request.method, request.url.path)
    return await call_next(request)


# ---- Endpoints ----
@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/integrantes")
def listar_integrantes():
    with get_conn() as conn:
        return conn.execute("SELECT nombre, carne FROM integrantes ORDER BY id").fetchall()


@app.get("/pacientes")
def listar_pacientes():
    with get_conn() as conn:
        return conn.execute(f"SELECT {COLUMNAS} FROM pacientes ORDER BY id").fetchall()


@app.get("/pacientes/{paciente_id}")
def obtener_paciente(paciente_id: int):
    with get_conn() as conn:
        fila = conn.execute(
            f"SELECT {COLUMNAS} FROM pacientes WHERE id = %s", (paciente_id,)
        ).fetchone()
    if fila is None:
        return error(404, "paciente no encontrado")
    return fila


@app.post("/pacientes", status_code=201)
def crear_paciente(p: PacienteIn):
    with get_conn() as conn:
        fila = conn.execute(
            f"""INSERT INTO pacientes
                (nombre, especie, raza, fecha_nacimiento, propietario_nombre, propietario_telefono)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING {COLUMNAS}""",
            (p.nombre, p.especie, p.raza, p.fecha_nacimiento,
             p.propietario_nombre, p.propietario_telefono),
        ).fetchone()
    return fila


@app.put("/pacientes/{paciente_id}")
def actualizar_paciente(paciente_id: int, p: PacienteIn):
    with get_conn() as conn:
        fila = conn.execute(
            f"""UPDATE pacientes SET nombre=%s, especie=%s, raza=%s, fecha_nacimiento=%s,
                propietario_nombre=%s, propietario_telefono=%s
                WHERE id=%s RETURNING {COLUMNAS}""",
            (p.nombre, p.especie, p.raza, p.fecha_nacimiento,
             p.propietario_nombre, p.propietario_telefono, paciente_id),
        ).fetchone()
    if fila is None:
        return error(404, "paciente no encontrado")
    return fila


@app.delete("/pacientes/{paciente_id}")
def eliminar_paciente(paciente_id: int):
    try:
        with get_conn() as conn:
            cur = conn.execute("DELETE FROM pacientes WHERE id = %s", (paciente_id,))
            borrados = cur.rowcount
    except psycopg.errors.ForeignKeyViolation:
        return error(409, "el paciente tiene citas asociadas y no puede eliminarse")
    if borrados == 0:
        return error(404, "paciente no encontrado")
    return Response(status_code=204)