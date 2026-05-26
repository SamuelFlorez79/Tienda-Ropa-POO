from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import uuid4


def dinero(valor):
    from decimal import Decimal
    return Decimal(str(valor))


@dataclass
class DetalleVenta:
    codigo_producto: str
    nombre_producto: str
    talla: str
    cantidad: int
    precio_unitario: Decimal
    costo_unitario: Decimal

    def __post_init__(self) -> None:
        self.codigo_producto = self.codigo_producto.strip().upper()
        self.nombre_producto = self.nombre_producto.strip()
        self.talla = self.talla.strip().upper()

        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        self.precio_unitario = dinero(self.precio_unitario)
        self.costo_unitario = dinero(self.costo_unitario)

        if not self.codigo_producto or not self.nombre_producto or not self.talla:
            raise ValueError("El detalle de venta esta incompleto")

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad

    @property
    def costo_total(self) -> Decimal:
        return self.costo_unitario * self.cantidad

    @property
    def ganancia_bruta(self) -> Decimal:
        return self.subtotal - self.costo_total


@dataclass
class LineaCarrito:
    codigo_producto: str
    nombre_producto: str
    categoria: str
    talla: str
    cantidad: int
    precio_unitario: Decimal

    def __post_init__(self) -> None:
        self.codigo_producto = self.codigo_producto.strip().upper()
        self.nombre_producto = self.nombre_producto.strip()
        self.categoria = self.categoria.strip().lower()
        self.talla = self.talla.strip().upper()
        self.precio_unitario = dinero(self.precio_unitario)

        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        if not self.codigo_producto or not self.nombre_producto or not self.categoria or not self.talla:
            raise ValueError("La linea de carrito esta incompleta")

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad

    @property
    def clave(self) -> tuple[str, str]:
        return self.codigo_producto, self.talla


@dataclass
class Venta:
    cliente
    empleado
    detalles: list[DetalleVenta] = field(default_factory=list)
    metodo_pago: str = "efectivo"
    fecha: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid4().hex[:12].upper())

    def __post_init__(self) -> None:
        self.metodo_pago = self.metodo_pago.strip() or "efectivo"
        self.id = self.id.strip().upper()

        if not self.detalles:
            raise ValueError("La venta debe incluir al menos un detalle")

    @property
    def total(self) -> Decimal:
        return sum((detalle.subtotal for detalle in self.detalles), Decimal("0"))

    @property
    def costo_total(self) -> Decimal:
        return sum((detalle.costo_total for detalle in self.detalles), Decimal("0"))

    @property
    def ganancia_bruta(self) -> Decimal:
        return self.total - self.costo_total

    @property
    def cantidad_items(self) -> int:
        return sum(detalle.cantidad for detalle in self.detalles)

    def resumen(self) -> str:
        return (
            f"{self.fecha:%Y-%m-%d %H:%M:%S} | venta {self.id} | "
            f"cliente={self.cliente.nombre} | empleado={self.empleado.nombre} | "
            f"total=${self.total:,.2f}"
        )
