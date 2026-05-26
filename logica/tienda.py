from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from logica.finanzas import Gasto, MovimientoCaja, TipoMovimiento
from logica.personas import Cliente, Empleado
from logica.producto import Producto
from logica.ventas import DetalleVenta, Venta


class EstadoTienda(str, Enum):
    ABIERTA = "abierta"
    CERRADA = "cerrada"


@dataclass
class RegistroEstadoTienda:
    estado: EstadoTienda
    fecha: datetime = field(default_factory=datetime.now)
    motivo: str = ""


@dataclass
class Tienda:
    nombre: str = "AJS Shop"
    __productos: dict[str, Producto] = field(default_factory=dict, init=False, repr=False)
    __empleados: dict[str, Empleado] = field(default_factory=dict, init=False, repr=False)
    __clientes: dict[str, Cliente] = field(default_factory=dict, init=False, repr=False)
    __ventas: list[Venta] = field(default_factory=list, init=False, repr=False)
    __gastos: list[Gasto] = field(default_factory=list, init=False, repr=False)
    __movimientos_caja: list[MovimientoCaja] = field(default_factory=list, init=False, repr=False)
    __registro_estado: list[RegistroEstadoTienda] = field(default_factory=list, init=False, repr=False)
    __estado: EstadoTienda = field(default=EstadoTienda.CERRADA, init=False, repr=False)

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip() or "AJS Shop"

    @property
    def estado(self) -> EstadoTienda:
        return self.__estado

    @property
    def esta_abierta(self) -> bool:
        return self.__estado == EstadoTienda.ABIERTA

    @property
    def productos(self):
        return tuple(self.__productos.values())

    @property
    def empleados(self):
        return tuple(self.__empleados.values())

    @property
    def clientes(self):
        return tuple(self.__clientes.values())

    @property
    def ventas(self):
        return tuple(self.__ventas)

    def abrir_tienda(self, motivo: str = "manual") -> bool:
        if self.__estado == EstadoTienda.ABIERTA:
            return False

        self.__estado = EstadoTienda.ABIERTA
        self.__registro_estado.append(
            RegistroEstadoTienda(
                estado=self.__estado,
                motivo=motivo
            )
        )

        return True

    def cerrar_tienda(self, motivo: str = "manual") -> bool:
        if self.__estado == EstadoTienda.CERRADA:
            return False

        self.__estado = EstadoTienda.CERRADA
        self.__registro_estado.append(
            RegistroEstadoTienda(
                estado=self.__estado,
                motivo=motivo
            )
        )

        return True

    def registrar_producto(self, producto: Producto) -> Producto:
        if producto.codigo in self.__productos:
            raise ValueError(f"Ya existe un producto con codigo {producto.codigo}")

        self.__productos[producto.codigo] = producto

        return producto

    def registrar_empleado(self, empleado: Empleado) -> Empleado:
        if empleado.documento in self.__empleados:
            raise ValueError(f"Ya existe un empleado con documento {empleado.documento}")

        self.__empleados[empleado.documento] = empleado

        return empleado

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        if cliente.documento in self.__clientes:
            raise ValueError(f"Ya existe un cliente con documento {cliente.documento}")

        self.__clientes[cliente.documento] = cliente

        return cliente

    def obtener_producto(self, codigo: str) -> Producto:
        clave = codigo.strip().upper()

        if clave not in self.__productos:
            raise KeyError(f"Producto no encontrado: {clave}")

        return self.__productos[clave]

    def obtener_empleado(self, documento: str) -> Empleado:
        clave = documento.strip()

        if clave not in self.__empleados:
            raise KeyError(f"Empleado no encontrado: {clave}")

        return self.__empleados[clave]

    def obtener_cliente(self, documento: str) -> Cliente:
        clave = documento.strip()

        if clave not in self.__clientes:
            raise KeyError(f"Cliente no encontrado: {clave}")

        return self.__clientes[clave]

    def registrar_gasto(
        self,
        concepto: str,
        monto,
        categoria: str = "general",
        responsable: str = "",
    ) -> Gasto:

        gasto = Gasto(
            concepto=concepto,
            monto=monto,
            categoria=categoria,
            responsable=responsable,
        )

        self.__gastos.append(gasto)

        self.__movimientos_caja.append(
            MovimientoCaja(
                tipo=TipoMovimiento.EGRESO,
                monto=gasto.monto,
                descripcion=gasto.concepto,
                referencia=gasto.categoria,
                fecha=gasto.fecha,
            )
        )

        return gasto

    @property
    def total_ventas(self) -> Decimal:
        return sum((venta.total for venta in self.__ventas), Decimal("0"))

    @property
    def total_gastos(self) -> Decimal:
        return sum((gasto.monto for gasto in self.__gastos), Decimal("0"))

    @property
    def caja_actual(self) -> Decimal:
        ingresos = sum(
            (
                movimiento.monto
                for movimiento in self.__movimientos_caja
                if movimiento.tipo == TipoMovimiento.INGRESO
            ),
            Decimal("0"),
        )

        egresos = sum(
            (
                movimiento.monto
                for movimiento in self.__movimientos_caja
                if movimiento.tipo == TipoMovimiento.EGRESO
            ),
            Decimal("0"),
        )

        return ingresos - egresos

    def resumen_operativo(self) -> str:
        return (
            f"Estado: {self.estado.value} | "
            f"Productos: {len(self.__productos)} | "
            f"Empleados: {len(self.__empleados)} | "
            f"Clientes: {len(self.__clientes)} | "
            f"Ventas: {len(self.__ventas)} | "
            f"Gastos: {len(self.__gastos)}"
        )
