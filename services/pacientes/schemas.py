from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PacienteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=50)
    raza: Optional[str] = Field(default=None, max_length=80)
    fecha_nacimiento: Optional[date] = None
    propietario_nombre: str = Field(min_length=1, max_length=120)
    propietario_telefono: Optional[str] = Field(default=None, max_length=20)

    @field_validator("raza", "fecha_nacimiento", "propietario_telefono", mode="before")
    @classmethod
    def vacio_a_none(cls, v):
        # El frontend puede mandar "" en campos opcionales
        if isinstance(v, str) and v.strip() == "":
            return None
        return v