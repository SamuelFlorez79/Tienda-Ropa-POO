from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4


def generar_codigo(prefijo: str) -> str:
    return f"{prefijo}{uuid4().hex[:8].upper()}"


def dinero(valor):
    from decimal import Decimal
    return Decimal(str(valor))


def formatear_moneda(valor: Decimal) -> str:
    return f"${valor:,.2f}"


@dataclass
class Marcaje:
    entrada: datetime = field(default_factory=datetime.now)
    salida: datetime | None = None

    @property
    def abierto(self) -> bool:
        return self.salida is None

    def cerrar(self, fecha: datetime | None = None) -> None:
        if self.salida is not None:
            raise ValueError("El marcaje ya fue cerrado")

        self.salida = fecha or datetime.now()

    @property
    def duracion(self) -> timedelta:
        fin = self.salida or datetime.now()
        return fin - self.entrada


@dataclass
class Cliente:
    nombre: str
    documento: str
    telefono: str = ""
    correo: str = ""
    fecha_registro: datetime = field(default_factory=datetime.now)
    codigo: str = field(default_factory=lambda: generar_codigo("C-"))
    _compras: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        self.documento = self.documento.strip()
        self.telefono = self.telefono.strip()
        self.correo = self.correo.strip()
        self.codigo = self.codigo.strip().upper()

        if not self.nombre:
            raise ValueError("El nombre del cliente no puede estar vacio")

        if not self.documento:
            raise ValueError("El documento del cliente no puede estar vacio")

    @property
    def compras(self):
        return tuple(self._compras)

    def registrar_compra(self, venta) -> None:
        self._compras.append(venta)

    @property
    def total_gastado(self) -> Decimal:
        total = Decimal("0")

        for venta in self._compras:
            total += venta.total

        return total

    @property
    def cantidad_compras(self) -> int:
        return len(self._compras)

    def resumen(self) -> str:
        return (
            f"{self.nombre} [{self.documento}] - compras={self.cantidad_compras}, "
            f"gastado={formatear_moneda(self.total_gastado)}"
        )


@dataclass
class Empleado:
    nombre: str
    documento: str
    cargo: str
    fecha_ingreso: datetime = field(default_factory=datetime.now)
    activo: bool = True
    codigo: str = field(default_factory=lambda: generar_codigo("E-"))
    _ventas: list = field(default_factory=list, init=False, repr=False)
    _marcajes: list[Marcaje] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        self.documento = self.documento.strip()
        self.cargo = self.cargo.strip()
        self.codigo = self.codigo.strip().upper()

        if not self.nombre:
            raise ValueError("El nombre del empleado no puede estar vacio")

        if not self.documento:
            raise ValueError("El documento del empleado no puede estar vacio")

        if not self.cargo:
            raise ValueError("El cargo del empleado no puede estar vacio")

    @property
    def ventas(self):
        return tuple(self._ventas)

    @property
    def marcajes(self):
        return tuple(self._marcajes)

    @property
    def esta_en_turno(self) -> bool:
        return any(marcaje.abierto for marcaje in self._marcajes)

    def registrar_ingreso(self, fecha: datetime | None = None) -> Marcaje:
        if self.esta_en_turno:
            raise ValueError("El empleado ya tiene un ingreso abierto")

        marcaje = Marcaje(entrada=fecha or datetime.now())
        self._marcajes.append(marcaje)

        return marcaje

    def registrar_salida(self, fecha: datetime | None = None) -> Marcaje:
        for marcaje in reversed(self._marcajes):
            if marcaje.abierto:
                marcaje.cerrar(fecha or datetime.now())
                return marcaje

        raise ValueError("No existe un ingreso abierto para cerrar")

    def registrar_venta(self, venta) -> None:
        self._ventas.append(venta)

    @property
    def total_vendido(self) -> Decimal:
        total = Decimal("0")

        for venta in self._ventas:
            total += venta.total

        return total

    @property
    def cantidad_ventas(self) -> int:
        return len(self._ventas)

    @property
    def tiempo_trabajado(self) -> timedelta:
        total = timedelta()

        for marcaje in self._marcajes:
            total += marcaje.duracion

        return total

    def resumen(self) -> str:
        estado = "en turno" if self.esta_en_turno else "fuera de turno"

        return (
            f"{self.nombre} [{self.documento}] - {self.cargo} - {estado}, "
            f"ventas={self.cantidad_ventas}, total={formatear_moneda(self.total_vendido)}"
        )
