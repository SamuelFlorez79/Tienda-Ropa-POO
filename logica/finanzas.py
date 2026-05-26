from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


def dinero(valor):
    from decimal import Decimal
    return Decimal(str(valor))


class TipoMovimiento(str, Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"


@dataclass
class Gasto:
    concepto: str
    monto: Decimal
    categoria: str = "general"
    responsable: str = ""
    fecha: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.concepto = self.concepto.strip()
        self.categoria = self.categoria.strip() or "general"
        self.responsable = self.responsable.strip()
        self.monto = dinero(self.monto)

        if not self.concepto:
            raise ValueError("El concepto del gasto no puede estar vacio")

        if self.monto <= 0:
            raise ValueError("El monto del gasto debe ser mayor que 0")


@dataclass
class MovimientoCaja:
    tipo: TipoMovimiento
    monto: Decimal
    descripcion: str
    referencia: str = ""
    fecha: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.descripcion = self.descripcion.strip()
        self.referencia = self.referencia.strip()
        self.monto = dinero(self.monto)

        if self.monto <= 0:
            raise ValueError("El monto del movimiento debe ser mayor que 0")

        if not self.descripcion:
            raise ValueError("La descripcion del movimiento no puede estar vacia")
