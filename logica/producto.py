from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from uuid import uuid4


def dinero(valor: object) -> Decimal:
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, (int, float, str)):
        texto = str(valor).strip().replace(",", ".")
        try:
            return Decimal(texto)
        except InvalidOperation as exc:
            raise ValueError(f"Valor monetario invalido: {valor!r}") from exc
    raise ValueError(f"Valor monetario invalido: {valor!r}")


def generar_codigo(prefijo: str) -> str:
    return f"{prefijo}{uuid4().hex[:8].upper()}"


def ordenar_tallas(tallas) -> list[str]:
    preferencia = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5}
    limpias = []

    for talla in tallas:
        texto = str(talla).strip().upper()
        if texto and texto not in limpias:
            limpias.append(texto)

    def clave(texto: str) -> tuple[int, int, str]:
        if texto.isdigit():
            return 0, int(texto), texto
        return 1, preferencia.get(texto, 999), texto

    limpias.sort(key=clave)
    return limpias


@dataclass
class InventarioTalla:
    bodega: int = 0
    tienda: int = 0

    def __post_init__(self) -> None:
        if self.bodega < 0 or self.tienda < 0:
            raise ValueError("El inventario no puede ser negativo")

    @property
    def total(self) -> int:
        return self.bodega + self.tienda

    def sumar_bodega(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        self.bodega += cantidad

    def sumar_tienda(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        self.tienda += cantidad

    def restar_bodega(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        if self.bodega < cantidad:
            raise ValueError("No hay suficiente stock en bodega")
        self.bodega -= cantidad

    def restar_tienda(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        if self.tienda < cantidad:
            raise ValueError("No hay suficiente stock en tienda")
        self.tienda -= cantidad


@dataclass
class Producto:
    nombre: str
    precio_venta: Decimal
    costo: Decimal
    categoria: str = "general"
    codigo: str = field(default_factory=lambda: generar_codigo("P-"))
    inventario: dict[str, InventarioTalla] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        self.categoria = self.categoria.strip().lower()
        self.codigo = self.codigo.strip().upper()
        self.precio_venta = dinero(self.precio_venta)
        self.costo = dinero(self.costo)

        if not self.nombre:
            raise ValueError("El nombre del producto no puede estar vacio")

        if not self.categoria:
            raise ValueError("La categoria del producto no puede estar vacia")

        if not self.codigo:
            raise ValueError("El codigo del producto no puede estar vacio")

        if self.precio_venta < 0 or self.costo < 0:
            raise ValueError("Los valores monetarios no pueden ser negativos")

    def _buscar_inventario(self, talla: str, crear: bool = False) -> InventarioTalla:
        clave = str(talla).strip().upper()

        if not clave:
            raise ValueError("La talla no puede estar vacia")

        if crear:
            if clave not in self.inventario:
                self.inventario[clave] = InventarioTalla()
            return self.inventario[clave]

        if clave not in self.inventario:
            raise KeyError(f"No existe la talla {clave} en el producto {self.nombre}")

        return self.inventario[clave]

    def agregar_talla(self, talla: str, bodega: int = 0, tienda: int = 0) -> None:
        if bodega < 0 or tienda < 0:
            raise ValueError("El stock inicial no puede ser negativo")

        inventario = self._buscar_inventario(talla, crear=True)
        inventario.bodega += bodega
        inventario.tienda += tienda

    def reponer_bodega(self, talla: str, cantidad: int) -> None:
        self._buscar_inventario(talla, crear=True).sumar_bodega(cantidad)

    def mover_a_tienda(self, talla: str, cantidad: int) -> None:
        inventario = self._buscar_inventario(talla)
        inventario.restar_bodega(cantidad)
        inventario.sumar_tienda(cantidad)

    def vender(self, talla: str, cantidad: int) -> None:
        inventario = self._buscar_inventario(talla)
        inventario.restar_tienda(cantidad)

    def stock_talla(self, talla: str) -> int:
        try:
            return self._buscar_inventario(talla).total
        except KeyError:
            return 0

    def stock_bodega(self, talla: str) -> int:
        try:
            return self._buscar_inventario(talla).bodega
        except KeyError:
            return 0

    def stock_tienda(self, talla: str) -> int:
        try:
            return self._buscar_inventario(talla).tienda
        except KeyError:
            return 0

    def stock_total(self) -> int:
        total = 0

        for inventario in self.inventario.values():
            total += inventario.total

        return total

    def resumen_inventario(self) -> str:
        if not self.inventario:
            return f"{self.categoria.title()} - {self.nombre} ({self.codigo}) sin tallas registradas"

        partes = []

        for talla in ordenar_tallas(self.inventario):
            inventario = self.inventario[talla]

            partes.append(
                f"{talla}: bodega={inventario.bodega}, tienda={inventario.tienda}, total={inventario.total}"
            )

        detalle = " | ".join(partes)

        return f"{self.categoria.title()} - {self.nombre} ({self.codigo}) -> {detalle}"
