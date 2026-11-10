"""Pruebas de la API de citas contra una base Postgres real.

Necesitan las variables DB_HOST, DB_PORT, DB_NAME, DB_USER y DB_PASSWORD y que
la base tenga las tablas de db/init.sql. Si no hay base, las pruebas se omiten.
"""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture(scope="module")
def cliente():
    try:
        db.esperar_base(intentos=2, pausa=1)
    except RuntimeError as exc:
        pytest.skip(f"sin base de datos: {exc}")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def nuevo_paciente():
    creados = []

    def crear(nombre="Firulais"):
        with db.conectar() as conn:
            fila = conn.execute(
                "INSERT INTO pacientes (nombre, especie, propietario_nombre) "
                "VALUES (%s, 'Perro', 'Propietario de prueba') RETURNING id",
                (nombre,),
            ).fetchone()
        creados.append(fila["id"])
        return fila["id"]

    yield crear

    with db.conectar() as conn:
        for pid in creados:
            conn.execute("DELETE FROM citas WHERE paciente_id = %s", (pid,))
            conn.execute("DELETE FROM pacientes WHERE id = %s", (pid,))


def cita(pid, **cambios):
    datos = {
        "paciente_id": pid,
        "fecha_hora": "2026-11-10T09:30:00",
        "motivo": "Vacuna anual",
        "veterinario": "Dra. Morales",
    }
    datos.update(cambios)
    return datos


def test_health(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["version"]


def test_crear_cita(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    r = cliente.post("/citas", json=cita(pid))
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["id"] > 0
    assert cuerpo["paciente_id"] == pid
    assert cuerpo["fecha_hora"] == "2026-11-10T09:30:00"
    assert cuerpo["motivo"] == "Vacuna anual"
    assert cuerpo["veterinario"] == "Dra. Morales"
    assert cuerpo["estado"] == "programada"


def test_crear_cita_con_paciente_inexistente(cliente):
    r = cliente.post("/citas", json=cita(999999))
    assert r.status_code == 400
    assert r.json() == {"error": "paciente no existe"}


@pytest.mark.parametrize(
    "cambios",
    [
        {"motivo": None},
        {"motivo": "   "},
        {"motivo": "x" * 201},
        {"estado": "pendiente"},
        {"fecha_hora": "mañana"},
        {"paciente_id": "abc"},
    ],
)
def test_validaciones_al_crear(cliente, nuevo_paciente, cambios):
    pid = nuevo_paciente()
    datos = cita(pid, **cambios)
    r = cliente.post("/citas", json=datos)
    assert r.status_code == 400
    assert r.json()["error"]


def test_campos_obligatorios(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    for campo in ("paciente_id", "fecha_hora", "motivo"):
        datos = cita(pid)
        del datos[campo]
        r = cliente.post("/citas", json=datos)
        assert r.status_code == 400, campo
        assert campo in r.json()["error"]


def test_cuerpo_que_no_es_json(cliente):
    r = cliente.post("/citas", content="esto no es json", headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_hora_con_zona_se_guarda_en_utc(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    r = cliente.post("/citas", json=cita(pid, fecha_hora="2026-11-10T09:30:00-06:00"))
    assert r.status_code == 201
    assert r.json()["fecha_hora"] == "2026-11-10T15:30:00"


def test_listar_y_filtrar_por_paciente(cliente, nuevo_paciente):
    a = nuevo_paciente("Luna")
    b = nuevo_paciente("Max")
    cliente.post("/citas", json=cita(a, motivo="Control"))
    cliente.post("/citas", json=cita(a, motivo="Vacuna"))
    cliente.post("/citas", json=cita(b, motivo="Cirugia"))

    todas = cliente.get("/citas").json()
    assert {c["paciente_id"] for c in todas} >= {a, b}

    de_a = cliente.get("/citas", params={"paciente_id": a}).json()
    assert len(de_a) == 2
    assert {c["paciente_id"] for c in de_a} == {a}

    assert cliente.get("/citas", params={"paciente_id": 999999}).json() == []
    r = cliente.get("/citas", params={"paciente_id": "uno"})
    assert r.status_code == 400


def test_obtener_cita(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    creada = cliente.post("/citas", json=cita(pid)).json()
    r = cliente.get(f"/citas/{creada['id']}")
    assert r.status_code == 200
    assert r.json() == creada

    r = cliente.get("/citas/999999")
    assert r.status_code == 404
    assert r.json() == {"error": "cita no encontrada"}


def test_actualizar_cita(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    otro = nuevo_paciente("Rocky")
    creada = cliente.post("/citas", json=cita(pid)).json()
    url = f"/citas/{creada['id']}"

    r = cliente.put(url, json={"estado": "completada"})
    assert r.status_code == 200
    assert r.json()["estado"] == "completada"
    assert r.json()["motivo"] == creada["motivo"]

    r = cliente.put(url, json=cita(otro, motivo="Revision", estado="cancelada"))
    assert r.status_code == 200
    assert r.json()["paciente_id"] == otro
    assert r.json()["motivo"] == "Revision"
    assert r.json()["estado"] == "cancelada"

    assert cliente.get(url).json()["estado"] == "cancelada"


def test_actualizar_con_datos_invalidos(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    url = f"/citas/{cliente.post('/citas', json=cita(pid)).json()['id']}"

    r = cliente.put(url, json={"paciente_id": 999999})
    assert r.status_code == 400
    assert r.json() == {"error": "paciente no existe"}

    assert cliente.put(url, json={"estado": "lista"}).status_code == 400
    assert cliente.put(url, json={"motivo": None}).status_code == 400
    assert cliente.get(url).json()["estado"] == "programada"


def test_actualizar_cita_inexistente(cliente):
    r = cliente.put("/citas/999999", json={"estado": "completada"})
    assert r.status_code == 404
    assert r.json() == {"error": "cita no encontrada"}


def test_eliminar_cita(cliente, nuevo_paciente):
    pid = nuevo_paciente()
    url = f"/citas/{cliente.post('/citas', json=cita(pid)).json()['id']}"

    r = cliente.delete(url)
    assert r.status_code == 204
    assert r.content == b""
    assert cliente.get(url).status_code == 404
    assert cliente.delete(url).status_code == 404


def test_ruta_inexistente(cliente):
    r = cliente.get("/nada")
    assert r.status_code == 404
    assert r.json() == {"error": "no encontrado"}
