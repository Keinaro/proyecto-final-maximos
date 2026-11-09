from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

ESTADOS = ("programada", "completada", "cancelada")
Estado = Literal["programada", "completada", "cancelada"]


def _sin_zona(valor):
    # La columna fecha_hora es TIMESTAMP sin zona: se guarda la hora en UTC.
    if valor is not None and valor.tzinfo is not None:
        return valor.astimezone(timezone.utc).replace(tzinfo=None)
    return valor


def _texto(valor):
    if valor is None:
        return valor
    valor = valor.strip()
    if not valor:
        raise ValueError("no puede estar vacio")
    return valor


class CitaNueva(BaseModel):
    paciente_id: int
    fecha_hora: datetime
    motivo: str = Field(max_length=200)
    veterinario: Optional[str] = Field(default=None, max_length=100)
    estado: Estado = "programada"

    @field_validator("fecha_hora")
    @classmethod
    def _fecha(cls, v):
        return _sin_zona(v)

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v):
        return _texto(v)

    @field_validator("veterinario")
    @classmethod
    def _veterinario(cls, v):
        return v.strip() or None if v is not None else None


class CitaCambios(BaseModel):
    paciente_id: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    motivo: Optional[str] = Field(default=None, max_length=200)
    veterinario: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[Estado] = None

    @field_validator("fecha_hora")
    @classmethod
    def _fecha(cls, v):
        return _sin_zona(v)

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v):
        return _texto(v)

    @field_validator("veterinario")
    @classmethod
    def _veterinario(cls, v):
        return v.strip() or None if v is not None else None

    @model_validator(mode="after")
    def _sin_nulos(self):
        for campo in ("paciente_id", "fecha_hora", "motivo", "estado"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser nulo")
        return self


def traducir_error(error):
    """Convierte el primer error de validacion de pydantic en un mensaje en espanol."""
    tipo = error.get("type", "")
    ruta = [str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path")]
    campo = ruta[0] if ruta else "cuerpo"

    if tipo == "json_invalid":
        return "el cuerpo no es un JSON valido"
    if tipo == "missing":
        return f"falta el campo {campo}"
    if tipo == "literal_error" and campo == "estado":
        return "estado invalido, valores permitidos: " + ", ".join(ESTADOS)
    if tipo.startswith("datetime"):
        return "fecha_hora debe estar en formato ISO 8601, por ejemplo 2026-11-10T09:30:00"
    if tipo.startswith("int"):
        return f"{campo} debe ser un numero entero"
    if tipo == "string_too_long":
        limite = error.get("ctx", {}).get("max_length")
        return f"{campo} no puede pasar de {limite} caracteres"
    if tipo in ("string_type", "model_attributes_type"):
        return f"{campo} tiene un tipo de dato invalido"
    if tipo == "value_error":
        return f"{campo}: " + str(error.get("msg", "")).removeprefix("Value error, ")
    return f"{campo}: {error.get('msg', 'valor invalido')}"
