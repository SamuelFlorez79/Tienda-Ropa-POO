from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from logica.tienda import Tienda

class _LegacyTiendaApp:
    OPEN_SECONDS = 8 * 60
    CLOSED_SECONDS = 30
    TICK_MS = 1000
    SIMULATED_SECONDS_PER_TICK = 10

    def __init__(self, root: tk.Tk, tienda: Tienda, demo: dict[str, str] | None = None) -> None:
        self.root = root
        self.tienda = tienda
        self.demo = demo or {}
        self._simulated_seconds = 0
        self._phase_seconds = 0
        self._auto_cycle = True

        self.root.title(f"{self.tienda.nombre} - Panel de control")
        self.root.geometry("1180x820")
        self.root.minsize(1120, 760)
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_aplicacion)

        self._estado_var = tk.StringVar()
        self._reloj_var = tk.StringVar()
        self._ciclo_var = tk.StringVar()
        self._resumen_var = tk.StringVar()
        self._auto_cycle_var = tk.BooleanVar(value=True)

        self._empleado_doc_var = tk.StringVar(value=self.demo.get("empleado", ""))
        self._empleado_nombre_var = tk.StringVar(value=self.demo.get("empleado_nombre", ""))
        self._empleado_cargo_var = tk.StringVar(value=self.demo.get("empleado_cargo", ""))

        self._cliente_nombre_var = tk.StringVar(value=self.demo.get("cliente_nombre", ""))
        self._cliente_doc_var = tk.StringVar(value=self.demo.get("cliente", ""))
        self._cliente_tel_var = tk.StringVar(value=self.demo.get("cliente_tel", ""))
        self._cliente_correo_var = tk.StringVar(value=self.demo.get("cliente_correo", ""))

        self._gasto_concepto_var = tk.StringVar()
        self._gasto_monto_var = tk.StringVar()
        self._gasto_categoria_var = tk.StringVar(value="general")

        self._venta_empleado_var = tk.StringVar(value=self.demo.get("empleado", ""))
        self._venta_cliente_nombre_var = tk.StringVar(value=self.demo.get("cliente_nombre", ""))
        self._venta_cliente_doc_var = tk.StringVar(value=self.demo.get("cliente", ""))
        self._venta_cliente_tel_var = tk.StringVar(value=self.demo.get("cliente_tel", ""))
        self._venta_cliente_correo_var = tk.StringVar(value=self.demo.get("cliente_correo", ""))
        self._venta_metodo_var = tk.StringVar(value="efectivo")

        self._marcaje_doc_var = tk.StringVar(value=self.demo.get("empleado", ""))
        self._items_text: ScrolledText | None = None
        self._inventario_text: ScrolledText | None = None
        self._log_text: ScrolledText | None = None

        self._construir_ui()
        self._sincronizar_interfaz()
        self._actualizar_textos()
        self._tick()

    def _construir_ui(self) -> None:
        contenedor = ttk.Frame(self.root, padding=12)
        contenedor.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)

        cabecera = ttk.Frame(contenedor)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(1, weight=1)

        ttk.Label(cabecera, textvariable=self._estado_var, font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(cabecera, textvariable=self._reloj_var, font=("Segoe UI", 13)).grid(row=0, column=1, sticky="e")
        ttk.Label(cabecera, textvariable=self._ciclo_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(cabecera, textvariable=self._resumen_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        panel_estado = ttk.Frame(cabecera)
        panel_estado.grid(row=0, column=2, rowspan=3, padx=(16, 0), sticky="e")
        ttk.Button(panel_estado, text="Abrir tienda", command=self._abrir_tienda_manual).grid(row=0, column=0, padx=3)
        ttk.Button(panel_estado, text="Cerrar tienda", command=self._cerrar_tienda_manual).grid(row=0, column=1, padx=3)
        ttk.Checkbutton(
            panel_estado,
            text="Ciclo automatico",
            variable=self._auto_cycle_var,
            command=self._cambiar_auto_ciclo,
        ).grid(row=0, column=2, padx=3)

        notebook = ttk.Notebook(contenedor)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(12, 8))

        pestaña_control = ttk.Frame(notebook, padding=10)
        pestaña_venta = ttk.Frame(notebook, padding=10)
        pestaña_registros = ttk.Frame(notebook, padding=10)
        notebook.add(pestaña_control, text="Control")
        notebook.add(pestaña_venta, text="Venta")
        notebook.add(pestaña_registros, text="Registros")

        self._construir_tab_control(pestaña_control)
        self._construir_tab_venta(pestaña_venta)
        self._construir_tab_registros(pestaña_registros)

        panel_inferior = ttk.Frame(contenedor)
        panel_inferior.grid(row=2, column=0, sticky="nsew")
        panel_inferior.columnconfigure(0, weight=1)
        panel_inferior.rowconfigure(0, weight=1)

        ttk.Label(panel_inferior, text="Eventos").grid(row=0, column=0, sticky="w")
        self._log_text = ScrolledText(panel_inferior, height=10, wrap="word", state="disabled")
        self._log_text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

    def _construir_tab_control(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)

        turno = ttk.LabelFrame(frame, text="Turno de empleados", padding=10)
        turno.grid(row=0, column=0, sticky="ew")
        turno.columnconfigure(1, weight=1)

        ttk.Label(turno, text="Documento").grid(row=0, column=0, sticky="w")
        ttk.Entry(turno, textvariable=self._marcaje_doc_var, width=20).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Button(turno, text="Marcar ingreso", command=self._marcar_ingreso).grid(row=0, column=2, padx=6)
        ttk.Button(turno, text="Marcar salida", command=self._marcar_salida).grid(row=0, column=3, padx=6)

        ttk.Label(
            turno,
            text="La venta requiere que el empleado exista, este activo y tenga el ingreso abierto.",
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

    def _construir_tab_venta(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        datos = ttk.LabelFrame(frame, text="Datos de la venta", padding=10)
        datos.grid(row=0, column=0, sticky="ew")
        for idx in range(6):
            datos.columnconfigure(idx, weight=1)

        self._fila_entry(datos, 0, "Empleado", self._venta_empleado_var, 0, width=18)
        self._fila_entry(datos, 1, "Cliente nombre", self._venta_cliente_nombre_var, 0, width=22)
        self._fila_entry(datos, 2, "Documento", self._venta_cliente_doc_var, 0, width=18)
        self._fila_entry(datos, 3, "Telefono", self._venta_cliente_tel_var, 0, width=18)
        self._fila_entry(datos, 4, "Correo", self._venta_cliente_correo_var, 0, width=24)

        ttk.Label(datos, text="Metodo de pago").grid(row=5, column=0, sticky="w", pady=(8, 0))
        metodo = ttk.Combobox(
            datos,
            textvariable=self._venta_metodo_var,
            values=("efectivo", "tarjeta", "transferencia"),
            state="readonly",
            width=18,
        )
        metodo.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        items = ttk.LabelFrame(frame, text="Items de la venta", padding=10)
        items.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        items.columnconfigure(0, weight=1)
        items.rowconfigure(1, weight=1)
        ttk.Label(items, text="Una linea por producto: codigo talla cantidad").grid(row=0, column=0, sticky="w")
        self._items_text = ScrolledText(items, height=10, wrap="none")
        self._items_text.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self._items_text.insert(
            "1.0",
            f"{self.demo.get('producto_camisa', '')} M 1\n{self.demo.get('producto_pantalon', '')} M 1",
        )

        acciones = ttk.Frame(frame)
        acciones.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(acciones, text="Registrar venta", command=self._registrar_venta).grid(row=0, column=0, sticky="w")

    def _construir_tab_registros(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        empleados = ttk.LabelFrame(frame, text="Empleado", padding=10)
        empleados.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 10))
        self._fila_entry(empleados, 0, "Nombre", self._empleado_nombre_var, 0, width=22)
        self._fila_entry(empleados, 1, "Documento", self._empleado_doc_var, 0, width=18)
        self._fila_entry(empleados, 2, "Cargo", self._empleado_cargo_var, 0, width=18)
        ttk.Button(empleados, text="Registrar empleado", command=self._registrar_empleado).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        clientes = ttk.LabelFrame(frame, text="Cliente", padding=10)
        clientes.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 10))
        self._fila_entry(clientes, 0, "Nombre", self._cliente_nombre_var, 0, width=22)
        self._fila_entry(clientes, 1, "Documento", self._cliente_doc_var, 0, width=18)
        self._fila_entry(clientes, 2, "Telefono", self._cliente_tel_var, 0, width=18)
        self._fila_entry(clientes, 3, "Correo", self._cliente_correo_var, 0, width=24)
        ttk.Button(clientes, text="Registrar cliente", command=self._registrar_cliente).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        gastos = ttk.LabelFrame(frame, text="Gasto", padding=10)
        gastos.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self._fila_entry(gastos, 0, "Concepto", self._gasto_concepto_var, 0, width=28)
        self._fila_entry(gastos, 1, "Monto", self._gasto_monto_var, 0, width=18)
        self._fila_entry(gastos, 2, "Categoria", self._gasto_categoria_var, 0, width=18)
        ttk.Button(gastos, text="Registrar gasto", command=self._registrar_gasto).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        inventario = ttk.LabelFrame(frame, text="Inventario", padding=10)
        inventario.grid(row=2, column=0, columnspan=2, sticky="nsew")
        inventario.columnconfigure(0, weight=1)
        inventario.rowconfigure(1, weight=1)
        ttk.Label(inventario, text="Resumen de productos, bodega y tienda").grid(row=0, column=0, sticky="w")
        self._inventario_text = ScrolledText(inventario, height=12, wrap="word", state="disabled")
        self._inventario_text.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _fila_entry(
        self,
        parent: ttk.Frame,
        fila: int,
        etiqueta: str,
        variable: tk.StringVar,
        columna: int,
        width: int = 20,
    ) -> None:
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=columna, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable, width=width).grid(row=fila, column=columna + 1, sticky="w", padx=(8, 18), pady=3)

    def _leer_items_venta(self) -> list[tuple[str, str, int]]:
        if self._items_text is None:
            raise RuntimeError("No se pudo acceder al formulario de items")
        lineas = []
        for numero, linea in enumerate(self._items_text.get("1.0", tk.END).splitlines(), start=1):
            texto = linea.strip()
            if not texto:
                continue
            partes = texto.replace(",", " ").split()
            if len(partes) != 3:
                raise ValueError(f"Linea {numero}: usa 'codigo talla cantidad'")
            codigo, talla, cantidad_texto = partes
            try:
                cantidad = int(cantidad_texto)
            except ValueError as exc:
                raise ValueError(f"Linea {numero}: la cantidad debe ser un numero entero") from exc
            lineas.append((codigo, talla, cantidad))
        if not lineas:
            raise ValueError("La venta debe tener al menos una linea de items")
        return lineas

    def _append_log(self, texto: str) -> None:
        if self._log_text is None:
            return
        self._log_text.configure(state="normal")
        self._log_text.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {texto}\n")
        self._log_text.see(tk.END)
        self._log_text.configure(state="disabled")

    def _sincronizar_interfaz(self) -> None:
        self._estado_var.set(f"Tienda {self.tienda.estado.value}")
        reloj = timedelta(seconds=self._simulated_seconds)
        total = int(reloj.total_seconds())
        horas, resto = divmod(total, 3600)
        minutos, segundos = divmod(resto, 60)
        self._reloj_var.set(f"Tiempo simulado {horas:02d}:{minutos:02d}:{segundos:02d}")
        modo = "activo" if self._auto_cycle else "manual"
        self._ciclo_var.set(
            f"Ciclo {modo} | abierta {self.OPEN_SECONDS // 60} min, cerrada {self.CLOSED_SECONDS} s, "
            f"avance {self.SIMULATED_SECONDS_PER_TICK} s por segundo real"
        )
        self._resumen_var.set(self.tienda.resumen_operativo())

    def _actualizar_textos(self) -> None:
        if self._inventario_text is not None:
            self._inventario_text.configure(state="normal")
            self._inventario_text.delete("1.0", tk.END)
            self._inventario_text.insert(tk.END, self.tienda.resumen_inventario() + "\n\n")
            self._inventario_text.insert(tk.END, "Empleados:\n")
            for empleado in self.tienda.empleados:
                self._inventario_text.insert(tk.END, f"- {empleado.resumen()}\n")
            self._inventario_text.insert(tk.END, "\nClientes:\n")
            for cliente in self.tienda.clientes:
                self._inventario_text.insert(tk.END, f"- {cliente.resumen()}\n")
            self._inventario_text.insert(tk.END, "\nVentas recientes:\n")
            for venta in self.tienda.ventas[-8:]:
                self._inventario_text.insert(tk.END, f"- {venta.resumen()}\n")
            self._inventario_text.configure(state="disabled")
        self._sincronizar_interfaz()

    def _abrir_tienda_manual(self) -> None:
        if self.tienda.abrir_tienda("manual"):
            self._append_log("La tienda se abrio manualmente")
        self._phase_seconds = 0
        self._actualizar_textos()

    def _cerrar_tienda_manual(self) -> None:
        if self.tienda.cerrar_tienda("manual"):
            self._append_log("La tienda se cerro manualmente")
        self._phase_seconds = 0
        self._actualizar_textos()

    def _cambiar_auto_ciclo(self) -> None:
        self._auto_cycle = self._auto_cycle_var.get()
        estado = "activo" if self._auto_cycle else "desactivado"
        self._append_log(f"Ciclo automatico {estado}")
        self._phase_seconds = 0
        self._actualizar_textos()

    def _marcar_ingreso(self) -> None:
        documento = self._marcaje_doc_var.get().strip()
        if not documento:
            messagebox.showerror("Empleado", "Escribe el documento del empleado")
            return
        try:
            empleado = self.tienda.obtener_empleado(documento)
            empleado.registrar_ingreso()
            self._append_log(f"Ingreso registrado para {empleado.nombre}")
            self._actualizar_textos()
        except Exception as exc:
            messagebox.showerror("Empleado", str(exc))

    def _marcar_salida(self) -> None:
        documento = self._marcaje_doc_var.get().strip()
        if not documento:
            messagebox.showerror("Empleado", "Escribe el documento del empleado")
            return
        try:
            empleado = self.tienda.obtener_empleado(documento)
            empleado.registrar_salida()
            self._append_log(f"Salida registrada para {empleado.nombre}")
            self._actualizar_textos()
        except Exception as exc:
            messagebox.showerror("Empleado", str(exc))

    def _registrar_empleado(self) -> None:
        try:
            empleado = Empleado(
                nombre=self._empleado_nombre_var.get(),
                documento=self._empleado_doc_var.get(),
                cargo=self._empleado_cargo_var.get(),
            )
            self.tienda.registrar_empleado(empleado)
            self._append_log(f"Empleado registrado: {empleado.resumen()}")
            self._actualizar_textos()
        except Exception as exc:
            messagebox.showerror("Empleado", str(exc))

    def _registrar_cliente(self) -> None:
        try:
            cliente = Cliente(
                nombre=self._cliente_nombre_var.get(),
                documento=self._cliente_doc_var.get(),
                telefono=self._cliente_tel_var.get(),
                correo=self._cliente_correo_var.get(),
            )
            self.tienda.registrar_cliente(cliente)
            self._append_log(f"Cliente registrado: {cliente.resumen()}")
            self._actualizar_textos()
        except Exception as exc:
            messagebox.showerror("Cliente", str(exc))

    def _registrar_gasto(self) -> None:
        try:
            gasto = self.tienda.registrar_gasto(
                concepto=self._gasto_concepto_var.get(),
                monto=self._gasto_monto_var.get(),
                categoria=self._gasto_categoria_var.get(),
            )
            self._append_log(f"Gasto registrado: {gasto.concepto} por {formatear_moneda(gasto.monto)}")
            self._gasto_concepto_var.set("")
            self._gasto_monto_var.set("")
            self._actualizar_textos()
        except Exception as exc:
            messagebox.showerror("Gasto", str(exc))

    def _registrar_venta(self) -> None:
        try:
            cliente = Cliente(
                nombre=self._venta_cliente_nombre_var.get(),
                documento=self._venta_cliente_doc_var.get(),
                telefono=self._venta_cliente_tel_var.get(),
                correo=self._venta_cliente_correo_var.get(),
            )
            items = self._leer_items_venta()
            venta = self.tienda.registrar_venta(
                empleado_documento=self._venta_empleado_var.get(),
                cliente=cliente,
                items=items,
                metodo_pago=self._venta_metodo_var.get(),
            )
            self._append_log(f"Venta registrada: {venta.resumen()}")
            self._actualizar_textos()
            if self._items_text is not None:
                self._items_text.delete("1.0", tk.END)
        except Exception as exc:
            messagebox.showerror("Venta", str(exc))

    def _tick(self) -> None:
        self._simulated_seconds += self.SIMULATED_SECONDS_PER_TICK

        if self._auto_cycle:
            self._phase_seconds += self.SIMULATED_SECONDS_PER_TICK
            if self.tienda.esta_abierta and self._phase_seconds >= self.OPEN_SECONDS:
                self.tienda.cerrar_tienda("ciclo automatico")
                self._append_log("La tienda cerro por ciclo automatico")
                self._phase_seconds = 0
            elif not self.tienda.esta_abierta and self._phase_seconds >= self.CLOSED_SECONDS:
                self.tienda.abrir_tienda("ciclo automatico")
                self._append_log("La tienda abrio por ciclo automatico")
                self._phase_seconds = 0

        self._actualizar_textos()
        self.root.after(self.TICK_MS, self._tick)

    def _cerrar_aplicacion(self) -> None:
        self.root.destroy()


def _formatear_tiempo(segundos: int) -> str:
    total = max(0, int(segundos))
    horas, resto = divmod(total, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def _campo_formulario(
    parent: ttk.Frame,
    fila: int,
    etiqueta: str,
    variable: tk.StringVar,
    ancho: int = 22,
    columna: int = 0,
) -> ttk.Entry:
    ttk.Label(parent, text=etiqueta).grid(row=fila, column=columna, sticky="w", pady=3)
    entrada = ttk.Entry(parent, textvariable=variable, width=ancho)
    entrada.grid(row=fila, column=columna + 1, sticky="ew", padx=(8, 16), pady=3)
    return entrada


def _texto_ro(widget: ScrolledText, contenido: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert(tk.END, contenido.rstrip() + ("\n" if contenido else ""))
    widget.configure(state="disabled")


class RolePanel(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "TiendaApp", titulo: str, subtitulo: str) -> None:
        super().__init__(master, padding=12)
        self.app = app
        self.tienda = app.tienda
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._acciones = self._crear_encabezado(titulo, subtitulo)
        self._cuerpo = ttk.Frame(self)
        self._cuerpo.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self._cuerpo.columnconfigure(0, weight=1)

    def _crear_encabezado(self, titulo: str, subtitulo: str) -> ttk.Frame:
        marco = ttk.Frame(self)
        marco.grid(row=0, column=0, sticky="ew")
        marco.columnconfigure(0, weight=1)

        info = ttk.Frame(marco)
        info.grid(row=0, column=0, sticky="w")
        ttk.Label(info, text=titulo, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(info, text=subtitulo).grid(row=1, column=0, sticky="w", pady=(2, 0))

        acciones = ttk.Frame(marco)
        acciones.grid(row=0, column=1, sticky="e")
        ttk.Button(acciones, text="Cambiar rol", command=self.app.mostrar_inicio).grid(row=0, column=0, padx=4)
        return acciones

    def refresh(self) -> None:
        return


class PantallaInicio(ttk.Frame):
    def __init__(self, master: tk.Misc, app: "TiendaApp") -> None:
        super().__init__(master, padding=18)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        marco = ttk.Frame(self)
        marco.grid(row=0, column=0, sticky="ew")
        marco.columnconfigure(0, weight=1)
        ttk.Label(marco, text="Eres cliente, empleado o gerente", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(marco, text="Selecciona tu perfil para abrir el panel correspondiente.").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )

        opciones = ttk.Frame(self)
        opciones.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
        for columna in range(3):
            opciones.columnconfigure(columna, weight=1)

        self._boton_perfil(opciones, 0, "Cliente", "Ver catalogo y registrar tu ficha", self.app.mostrar_cliente)
        self._boton_perfil(opciones, 1, "Empleado", "Registrar ventas y turnos", self.app.mostrar_empleado)
        self._boton_perfil(opciones, 2, "Gerente", "Gestionar empleados, gastos y caja", self.app.mostrar_gerente)

        ttk.Button(self, text="Salir", command=self.app.cerrar_aplicacion).grid(row=2, column=0, sticky="e", pady=(18, 0))

    def _boton_perfil(
        self,
        parent: ttk.Frame,
        columna: int,
        titulo: str,
        descripcion: str,
        comando,
    ) -> None:
        contenedor = ttk.Frame(parent, padding=12)
        contenedor.grid(row=0, column=columna, sticky="nsew", padx=6)
        contenedor.columnconfigure(0, weight=1)
        ttk.Label(contenedor, text=titulo, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(contenedor, text=descripcion, wraplength=220, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 10))
        ttk.Button(contenedor, text=f"Entrar como {titulo.lower()}", command=comando).grid(row=2, column=0, sticky="ew")


class PanelCliente(RolePanel):
    CATEGORIAS = (("camisas", "Camisas"), ("pantalones", "Pantalones"), ("zapatos", "Zapatos"))

    def __init__(self, master: tk.Misc, app: "TiendaApp") -> None:
        super().__init__(master, app, "Panel de cliente", "Catalogo publico y carrito de compras.")
        self._cliente_nombre_var = tk.StringVar()
        self._cliente_documento_var = tk.StringVar()
        self._cliente_telefono_var = tk.StringVar()
        self._cliente_correo_var = tk.StringVar()
        self._cliente_estado_var = tk.StringVar(value="Completa el registro para continuar.")
        self._cliente_activo: Cliente | None = None
        self._fase = 1
        self._fase_registro_frame: ttk.Frame | None = None
        self._fase_compra_frame: ttk.Frame | None = None

        self._carrito: dict[tuple[str, str], LineaCarrito] = {}
        self._carrito_tree: ttk.Treeview | None = None
        self._items_var = tk.StringVar(value="0 items")
        self._total_var = tk.StringVar(value=formatear_moneda(Decimal("0")))

        self._productos_por_categoria: dict[str, dict[str, Producto]] = {}
        self._producto_var_por_categoria: dict[str, tk.StringVar] = {}
        self._talla_var_por_categoria: dict[str, tk.StringVar] = {}
        self._cantidad_var_por_categoria: dict[str, tk.StringVar] = {}
        self._combo_producto_por_categoria: dict[str, ttk.Combobox] = {}
        self._combo_talla_por_categoria: dict[str, ttk.Combobox] = {}
        self._texto_categoria_por_categoria: dict[str, ScrolledText] = {}

        self._construir_interfaz()
        self.refresh()

    def _construir_interfaz(self) -> None:
        self._cuerpo.rowconfigure(0, weight=1)

        self._fase_registro_frame = ttk.Frame(self._cuerpo)
        self._fase_compra_frame = ttk.Frame(self._cuerpo)
        self._fase_registro_frame.grid(row=0, column=0, sticky="nsew")
        self._fase_compra_frame.grid(row=0, column=0, sticky="nsew")

        self._construir_fase_registro(self._fase_registro_frame)
        self._construir_fase_compra(self._fase_compra_frame)
        self._mostrar_fase_registro()

    def _construir_fase_registro(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        encabezado = ttk.Frame(frame)
        encabezado.grid(row=0, column=0, sticky="ew")
        encabezado.columnconfigure(0, weight=1)
        ttk.Label(encabezado, text="Primera fase", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(encabezado, text="Registra al cliente antes de entrar al catalogo y al carrito.").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )

        cliente = ttk.LabelFrame(frame, text="Registro de cliente", padding=10)
        cliente.grid(row=1, column=0, sticky="nw", pady=(12, 0))
        cliente.columnconfigure(1, weight=1)

        ttk.Label(cliente, textvariable=self._cliente_estado_var).grid(row=0, column=0, columnspan=2, sticky="w")
        _campo_formulario(cliente, 1, "Nombre", self._cliente_nombre_var, ancho=24)
        _campo_formulario(cliente, 2, "Documento", self._cliente_documento_var, ancho=24)
        _campo_formulario(cliente, 3, "Telefono", self._cliente_telefono_var, ancho=24)
        _campo_formulario(cliente, 4, "Correo", self._cliente_correo_var, ancho=28)

        acciones = ttk.Frame(cliente)
        acciones.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(acciones, text="Registrar / usar cliente", command=self._registrar_o_usar_cliente).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(acciones, text="Actualizar", command=self.refresh).grid(row=0, column=1)

    def _construir_fase_compra(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(frame)
        notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        for categoria, titulo in self.CATEGORIAS:
            tab = ttk.Frame(notebook, padding=10)
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(1, weight=1)
            notebook.add(tab, text=titulo)
            self._crear_tab_categoria(tab, categoria, titulo)

        carrito = ttk.LabelFrame(frame, text="Carrito de compras", padding=10)
        carrito.grid(row=0, column=1, sticky="nsew")
        carrito.columnconfigure(0, weight=1)
        carrito.rowconfigure(1, weight=1)

        resumen = ttk.Frame(carrito)
        resumen.grid(row=0, column=0, sticky="ew")
        resumen.columnconfigure(0, weight=1)
        resumen.columnconfigure(1, weight=1)
        ttk.Label(resumen, textvariable=self._items_var).grid(row=0, column=0, sticky="w")
        ttk.Label(resumen, textvariable=self._total_var).grid(row=0, column=1, sticky="e")

        columnas = ("codigo", "producto", "categoria", "talla", "cantidad", "precio", "subtotal")
        self._carrito_tree = ttk.Treeview(carrito, columns=columnas, show="headings", height=14)
        for col, texto, ancho in (
            ("codigo", "Codigo", 90),
            ("producto", "Producto", 170),
            ("categoria", "Categoria", 90),
            ("talla", "Talla", 70),
            ("cantidad", "Cant.", 60),
            ("precio", "Precio", 90),
            ("subtotal", "Subtotal", 100),
        ):
            self._carrito_tree.heading(col, text=texto)
            self._carrito_tree.column(col, width=ancho, anchor="center")
        self._carrito_tree.grid(row=1, column=0, sticky="nsew", pady=(10, 10))

        botones = ttk.Frame(carrito)
        botones.grid(row=2, column=0, sticky="ew")
        botones.columnconfigure(0, weight=1)
        ttk.Button(botones, text="+", width=4, command=self._sumar_unidad).grid(row=0, column=0, sticky="w", padx=(0, 4))
        ttk.Button(botones, text="-", width=4, command=self._restar_unidad).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Button(botones, text="Quitar", command=self._quitar_linea).grid(row=0, column=2, sticky="w", padx=4)
        ttk.Button(botones, text="Vaciar", command=self._vaciar_carrito).grid(row=0, column=3, sticky="w", padx=4)
        ttk.Button(botones, text="Pagar", command=self._pagar_carrito).grid(row=0, column=4, sticky="e", padx=(4, 0))

    def _mostrar_fase_registro(self) -> None:
        self._fase = 1
        if self._fase_compra_frame is not None:
            self._fase_compra_frame.grid_remove()
        if self._fase_registro_frame is not None:
            self._fase_registro_frame.grid()

    def _mostrar_fase_compra(self) -> None:
        self._fase = 2
        if self._fase_registro_frame is not None:
            self._fase_registro_frame.grid_remove()
        if self._fase_compra_frame is not None:
            self._fase_compra_frame.grid()
        self.refresh()

    def _crear_tab_categoria(self, tab: ttk.Frame, categoria: str, titulo: str) -> None:
        control = ttk.LabelFrame(tab, text=titulo, padding=10)
        control.grid(row=0, column=0, sticky="ew")
        control.columnconfigure(1, weight=1)

        producto_var = tk.StringVar()
        talla_var = tk.StringVar()
        cantidad_var = tk.StringVar(value="1")
        self._producto_var_por_categoria[categoria] = producto_var
        self._talla_var_por_categoria[categoria] = talla_var
        self._cantidad_var_por_categoria[categoria] = cantidad_var

        ttk.Label(control, text="Producto").grid(row=0, column=0, sticky="w", pady=3)
        combo_producto = ttk.Combobox(control, textvariable=producto_var, state="readonly", width=30)
        combo_producto.grid(row=0, column=1, sticky="ew", padx=(8, 16), pady=3)
        combo_producto.bind("<<ComboboxSelected>>", lambda _evento, cat=categoria: self._actualizar_categoria(cat))
        self._combo_producto_por_categoria[categoria] = combo_producto

        ttk.Label(control, text="Talla").grid(row=1, column=0, sticky="w", pady=3)
        combo_talla = ttk.Combobox(control, textvariable=talla_var, state="readonly", width=12)
        combo_talla.grid(row=1, column=1, sticky="w", padx=(8, 16), pady=3)
        self._combo_talla_por_categoria[categoria] = combo_talla

        ttk.Label(control, text="Cantidad").grid(row=2, column=0, sticky="w", pady=3)
        cantidad = ttk.Spinbox(control, from_=1, to=99, textvariable=cantidad_var, width=8)
        cantidad.grid(row=2, column=1, sticky="w", padx=(8, 16), pady=3)

        ttk.Button(control, text="Agregar al carrito", command=lambda cat=categoria: self._agregar_al_carrito(cat)).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        catalogo = ttk.LabelFrame(tab, text="Catalogo", padding=10)
        catalogo.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        catalogo.columnconfigure(0, weight=1)
        catalogo.rowconfigure(0, weight=1)
        texto = ScrolledText(catalogo, height=14, wrap="word", state="disabled")
        texto.grid(row=0, column=0, sticky="nsew")
        self._texto_categoria_por_categoria[categoria] = texto

    def _etiqueta_producto(self, producto: Producto) -> str:
        return f"{producto.codigo} - {producto.nombre}"

    def _producto_seleccionado(self, categoria: str) -> Producto | None:
        mapa = self._productos_por_categoria.get(categoria, {})
        clave = self._producto_var_por_categoria[categoria].get()
        return mapa.get(clave)

    def _actualizar_categoria(self, categoria: str) -> None:
        productos = self.tienda.productos_por_categoria(categoria)
        mapa = {self._etiqueta_producto(producto): producto for producto in productos}
        self._productos_por_categoria[categoria] = mapa

        combo_producto = self._combo_producto_por_categoria[categoria]
        combo_talla = self._combo_talla_por_categoria[categoria]
        producto_var = self._producto_var_por_categoria[categoria]
        talla_var = self._talla_var_por_categoria[categoria]

        opciones = tuple(mapa.keys())
        combo_producto["values"] = opciones
        if not opciones:
            producto_var.set("")
            combo_talla["values"] = ()
            talla_var.set("")
            _texto_ro(self._texto_categoria_por_categoria[categoria], self.app.texto_catalogo_categoria(categoria))
            return

        if producto_var.get() not in mapa:
            producto_var.set(opciones[0])

        producto = mapa[producto_var.get()]
        tallas = [talla for talla in ordenar_tallas(producto.inventario) if producto.stock_tienda(talla) > 0]
        combo_talla["values"] = tuple(tallas)
        if not tallas:
            talla_var.set("")
        elif talla_var.get() not in tallas:
            talla_var.set(tallas[0])

        _texto_ro(self._texto_categoria_por_categoria[categoria], self.app.texto_catalogo_categoria(categoria))

    def _actualizar_cliente_estado(self) -> None:
        if self._cliente_activo is None:
            self._cliente_estado_var.set("Cliente activo: sin registrar")
        else:
            self._cliente_estado_var.set(
                f"Cliente activo: {self._cliente_activo.nombre} [{self._cliente_activo.documento}]"
            )

    def _leer_cantidad(self, categoria: str) -> int:
        texto = self._cantidad_var_por_categoria[categoria].get().strip()
        try:
            cantidad = int(texto)
        except ValueError as exc:
            raise ValueError("La cantidad debe ser un numero entero") from exc
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        return cantidad

    def _asegurar_cliente_activo(self) -> tuple[Cliente, bool]:
        documento = self._cliente_documento_var.get().strip()
        nombre = self._cliente_nombre_var.get().strip()
        telefono = self._cliente_telefono_var.get().strip()
        correo = self._cliente_correo_var.get().strip()

        if not documento:
            raise ValueError("El documento del cliente es obligatorio")

        try:
            cliente = self.tienda.obtener_cliente(documento)
            self._cliente_nombre_var.set(cliente.nombre)
            self._cliente_telefono_var.set(cliente.telefono)
            self._cliente_correo_var.set(cliente.correo)
            nuevo = False
        except ClienteNoEncontradoError:
            if not nombre:
                raise ValueError("El nombre del cliente es obligatorio para registrarlo")
            cliente = Cliente(nombre=nombre, documento=documento, telefono=telefono, correo=correo)
            self.tienda.registrar_cliente(cliente)
            nuevo = True

        self._cliente_activo = cliente
        self._actualizar_cliente_estado()
        return cliente, nuevo

    def _registrar_o_usar_cliente(self) -> None:
        try:
            cliente, nuevo = self._asegurar_cliente_activo()
            mensaje = "registrado con exito" if nuevo else "cliente ya registrado"
            self.app.mostrar_mensaje(f"Cliente listo: {cliente.nombre}")
            messagebox.showinfo("Cliente", mensaje)
            self._mostrar_fase_compra()
        except Exception as exc:
            messagebox.showerror("Cliente", str(exc))

    def _agregar_al_carrito(self, categoria: str) -> None:
        try:
            producto = self._producto_seleccionado(categoria)
            if producto is None:
                raise ValueError("Debes seleccionar un producto")

            talla = self._talla_var_por_categoria[categoria].get().strip().upper()
            if not talla:
                raise ValueError("Debes seleccionar una talla")

            cantidad = self._leer_cantidad(categoria)
            disponible = producto.stock_tienda(talla)
            actual = self._carrito.get((producto.codigo, talla))
            cantidad_en_carrito = actual.cantidad if actual is not None else 0
            if cantidad_en_carrito + cantidad > disponible:
                raise ValueError(
                    f"No hay stock suficiente de {producto.nombre} talla {talla}. "
                    f"Disponibles: {disponible}, en carrito: {cantidad_en_carrito}"
                )

            clave = (producto.codigo, talla)
            if actual is None:
                self._carrito[clave] = LineaCarrito(
                    codigo_producto=producto.codigo,
                    nombre_producto=producto.nombre,
                    categoria=producto.categoria,
                    talla=talla,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                )
            else:
                actual.cantidad += cantidad

            self.app.mostrar_mensaje(f"Agregado al carrito: {producto.nombre} talla {talla}")
            self._refrescar_carrito()
        except Exception as exc:
            messagebox.showerror("Carrito", str(exc))

    def _linea_seleccionada(self) -> tuple[str, str] | None:
        if self._carrito_tree is None:
            return None
        seleccion = self._carrito_tree.selection()
        if not seleccion:
            return None
        codigo, talla = seleccion[0].split("::", 1)
        return codigo, talla

    def _cambiar_cantidad_linea(self, delta: int) -> None:
        clave = self._linea_seleccionada()
        if clave is None:
            messagebox.showerror("Carrito", "Selecciona una linea del carrito")
            return

        linea = self._carrito.get(clave)
        if linea is None:
            self._refrescar_carrito()
            return

        producto = self.tienda.obtener_producto(linea.codigo_producto)
        nueva = linea.cantidad + delta

        if delta > 0:
            disponible = producto.stock_tienda(linea.talla)
            if nueva > disponible:
                messagebox.showerror(
                    "Carrito",
                    f"No hay stock suficiente de {producto.nombre} talla {linea.talla}.",
                )
                return

        if nueva <= 0:
            del self._carrito[clave]
        else:
            linea.cantidad = nueva

        self._refrescar_carrito()

    def _sumar_unidad(self) -> None:
        self._cambiar_cantidad_linea(1)

    def _restar_unidad(self) -> None:
        self._cambiar_cantidad_linea(-1)

    def _quitar_linea(self) -> None:
        clave = self._linea_seleccionada()
        if clave is None:
            messagebox.showerror("Carrito", "Selecciona una linea del carrito")
            return
        self._carrito.pop(clave, None)
        self._refrescar_carrito()

    def _vaciar_carrito(self) -> None:
        self._carrito.clear()
        self._refrescar_carrito()

    def _refrescar_carrito(self) -> None:
        if self._carrito_tree is None:
            return

        seleccion = self._carrito_tree.selection()
        seleccionado = seleccion[0] if seleccion else ""

        for item in self._carrito_tree.get_children():
            self._carrito_tree.delete(item)

        total_items = 0
        total = Decimal("0")
        for linea in self._carrito.values():
            iid = f"{linea.codigo_producto}::{linea.talla}"
            self._carrito_tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    linea.codigo_producto,
                    linea.nombre_producto,
                    linea.categoria.title(),
                    linea.talla,
                    linea.cantidad,
                    formatear_moneda(linea.precio_unitario),
                    formatear_moneda(linea.subtotal),
                ),
            )
            total_items += linea.cantidad
            total += linea.subtotal

        if seleccionado and self._carrito_tree.exists(seleccionado):
            self._carrito_tree.selection_set(seleccionado)

        self._items_var.set(f"{total_items} item{'s' if total_items != 1 else ''}")
        self._total_var.set(f"Total: {formatear_moneda(total)}")

    def _pagar_carrito(self) -> None:
        try:
            if not self._carrito:
                raise ValueError("El carrito esta vacio")
            cliente, _ = self._asegurar_cliente_activo()
            empleado = self.tienda.empleado_en_turno()
            if empleado is None:
                self.app.mostrar_mensaje("no hay empleados en turno")
                messagebox.showwarning("Venta", "no hay empleados en turno")
                return

            metodo_pago = self.app.solicitar_metodo_pago()
            if metodo_pago is None:
                return

            if not messagebox.askyesno(
                "Pagar carrito",
                f"Confirmar pago con {metodo_pago.title()} por {cliente.nombre} por {self._total_var.get()}?",
            ):
                return

            items = [(linea.codigo_producto, linea.talla, linea.cantidad) for linea in self._carrito.values()]
            venta = self.tienda.registrar_venta(empleado.documento, cliente, items, metodo_pago=metodo_pago)
            self._carrito.clear()
            self._refrescar_carrito()
            self.refresh()
            self.app.mostrar_mensaje(f"Venta registrada: {venta.id}")
            messagebox.showinfo(
                "Venta",
                f"Venta registrada por {empleado.nombre}. Total: {formatear_moneda(venta.total)}",
            )
        except Exception as exc:
            messagebox.showerror("Venta", str(exc))

    def refresh(self) -> None:
        self._actualizar_cliente_estado()
        for categoria, _titulo in self.CATEGORIAS:
            self._actualizar_categoria(categoria)
        self._refrescar_carrito()


class PanelEmpleado(RolePanel):
    def __init__(self, master: tk.Misc, app: "TiendaApp") -> None:
        super().__init__(master, app, "Panel de empleado", "Ventas, turnos y registro de clientes.")
        self._empleado_doc_var = tk.StringVar()
        self._cliente_nombre_var = tk.StringVar()
        self._cliente_doc_var = tk.StringVar()
        self._cliente_tel_var = tk.StringVar()
        self._cliente_correo_var = tk.StringVar()
        self._metodo_pago_var = tk.StringVar()
        self._stock_producto_var = tk.StringVar()
        self._stock_talla_var = tk.StringVar()
        self._stock_cantidad_var = tk.StringVar(value="1")
        self._items_text: ScrolledText | None = None
        self._stock_text: ScrolledText | None = None
        self._inventario_text: ScrolledText | None = None
        self._stock_productos: dict[str, Producto] = {}
        self._stock_combo_producto: ttk.Combobox | None = None
        self._stock_combo_talla: ttk.Combobox | None = None

        turno = ttk.LabelFrame(self._cuerpo, text="Turno", padding=10)
        turno.grid(row=0, column=0, sticky="ew")
        turno.columnconfigure(1, weight=1)
        _campo_formulario(turno, 0, "Documento empleado", self._empleado_doc_var, ancho=24)
        ttk.Button(turno, text="Registrar ingreso", command=self._registrar_ingreso).grid(row=0, column=2, padx=(4, 0))
        ttk.Button(turno, text="Registrar salida", command=self._registrar_salida).grid(row=0, column=3, padx=(4, 0))

        notebook = ttk.Notebook(self._cuerpo)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self._cuerpo.rowconfigure(1, weight=1)

        tab_venta = ttk.Frame(notebook, padding=10)
        tab_cliente = ttk.Frame(notebook, padding=10)
        tab_stock = ttk.Frame(notebook, padding=10)
        tab_inventario = ttk.Frame(notebook, padding=10)
        tab_venta.columnconfigure(1, weight=1)
        tab_venta.rowconfigure(1, weight=1)
        tab_cliente.columnconfigure(1, weight=1)
        tab_stock.columnconfigure(0, weight=1)
        tab_stock.rowconfigure(1, weight=1)
        tab_inventario.columnconfigure(0, weight=1)
        tab_inventario.rowconfigure(0, weight=1)
        notebook.add(tab_venta, text="Venta")
        notebook.add(tab_cliente, text="Clientes")
        notebook.add(tab_stock, text="Stock")
        notebook.add(tab_inventario, text="Inventario")

        venta = ttk.LabelFrame(tab_venta, text="Registrar venta", padding=10)
        venta.grid(row=0, column=0, sticky="ew")
        venta.columnconfigure(1, weight=1)
        _campo_formulario(venta, 0, "Empleado", self._empleado_doc_var, ancho=24)
        _campo_formulario(venta, 1, "Cliente nombre", self._cliente_nombre_var, ancho=24)
        _campo_formulario(venta, 2, "Cliente doc.", self._cliente_doc_var, ancho=24)
        _campo_formulario(venta, 3, "Telefono", self._cliente_tel_var, ancho=24)
        _campo_formulario(venta, 4, "Correo", self._cliente_correo_var, ancho=28)
        ttk.Label(venta, text="Metodo de pago").grid(row=5, column=0, sticky="w", pady=3)
        metodo = ttk.Combobox(
            venta,
            textvariable=self._metodo_pago_var,
            values=("efectivo", "tarjeta", "transferencia"),
            state="readonly",
            width=20,
        )
        metodo.grid(row=5, column=1, sticky="w", padx=(8, 16), pady=3)

        detalles = ttk.LabelFrame(tab_venta, text="Items", padding=10)
        detalles.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        detalles.columnconfigure(0, weight=1)
        detalles.rowconfigure(1, weight=1)
        ttk.Label(detalles, text="Formato: codigo talla cantidad").grid(row=0, column=0, sticky="w")
        self._items_text = ScrolledText(detalles, height=10, wrap="none")
        self._items_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        ttk.Button(detalles, text="Registrar venta", command=self._registrar_venta).grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )

        cliente = ttk.LabelFrame(tab_cliente, text="Registrar cliente", padding=10)
        cliente.grid(row=0, column=0, sticky="ew")
        cliente.columnconfigure(1, weight=1)
        _campo_formulario(cliente, 0, "Nombre", self._cliente_nombre_var, ancho=24)
        _campo_formulario(cliente, 1, "Documento", self._cliente_doc_var, ancho=24)
        _campo_formulario(cliente, 2, "Telefono", self._cliente_tel_var, ancho=24)
        _campo_formulario(cliente, 3, "Correo", self._cliente_correo_var, ancho=28)
        ttk.Button(cliente, text="Registrar cliente", command=self._registrar_cliente).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        stock = ttk.LabelFrame(tab_stock, text="Movimiento de stock", padding=10)
        stock.grid(row=0, column=0, sticky="ew")
        stock.columnconfigure(1, weight=1)
        ttk.Label(stock, text="Producto").grid(row=0, column=0, sticky="w", pady=3)
        self._stock_combo_producto = ttk.Combobox(stock, textvariable=self._stock_producto_var, state="readonly", width=34)
        self._stock_combo_producto.grid(row=0, column=1, sticky="ew", padx=(8, 16), pady=3)
        self._stock_combo_producto.bind("<<ComboboxSelected>>", lambda _evento: self._actualizar_stock_tallas())

        ttk.Label(stock, text="Talla").grid(row=1, column=0, sticky="w", pady=3)
        self._stock_combo_talla = ttk.Combobox(stock, textvariable=self._stock_talla_var, state="readonly", width=12)
        self._stock_combo_talla.grid(row=1, column=1, sticky="w", padx=(8, 16), pady=3)

        ttk.Label(stock, text="Cantidad").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Spinbox(stock, from_=1, to=99, textvariable=self._stock_cantidad_var, width=8).grid(
            row=2, column=1, sticky="w", padx=(8, 16), pady=3
        )

        acciones_stock = ttk.Frame(stock)
        acciones_stock.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(acciones_stock, text="Recibir en bodega", command=self._recibir_stock_bodega).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(acciones_stock, text="Llevar a tienda", command=self._pasar_stock_a_tienda).grid(
            row=0, column=1, padx=6
        )

        inventario_stock = ttk.LabelFrame(tab_stock, text="Inventario actual", padding=10)
        inventario_stock.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        inventario_stock.columnconfigure(0, weight=1)
        inventario_stock.rowconfigure(0, weight=1)
        self._stock_text = ScrolledText(inventario_stock, height=14, wrap="word", state="disabled")
        self._stock_text.grid(row=0, column=0, sticky="nsew")

        inventario = ttk.LabelFrame(tab_inventario, text="Catalogo operativo", padding=10)
        inventario.grid(row=0, column=0, sticky="nsew")
        inventario.columnconfigure(0, weight=1)
        inventario.rowconfigure(1, weight=1)
        ttk.Label(inventario, text="Inventario visible para la operacion diaria.").grid(row=0, column=0, sticky="w")
        self._inventario_text = ScrolledText(inventario, height=18, wrap="word", state="disabled")
        self._inventario_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        ttk.Button(inventario, text="Actualizar", command=self.refresh).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def refresh(self) -> None:
        self._actualizar_stock_catalogo()
        if self._inventario_text is not None:
            _texto_ro(self._inventario_text, self.app.texto_catalogo_operativo())

    def _registrar_ingreso(self) -> None:
        try:
            empleado = self.tienda.obtener_empleado(self._empleado_doc_var.get())
            empleado.registrar_ingreso()
            self.app.mostrar_mensaje(f"Ingreso registrado para {empleado.nombre}")
            messagebox.showinfo("Turno", f"Ingreso registrado para {empleado.nombre}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Turno", str(exc))

    def _registrar_salida(self) -> None:
        try:
            empleado = self.tienda.obtener_empleado(self._empleado_doc_var.get())
            empleado.registrar_salida()
            self.app.mostrar_mensaje(f"Salida registrada para {empleado.nombre}")
            messagebox.showinfo("Turno", f"Salida registrada para {empleado.nombre}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Turno", str(exc))

    def _registrar_cliente(self) -> None:
        try:
            cliente = Cliente(
                nombre=self._cliente_nombre_var.get(),
                documento=self._cliente_doc_var.get(),
                telefono=self._cliente_tel_var.get(),
                correo=self._cliente_correo_var.get(),
            )
            self.tienda.registrar_cliente(cliente)
            self.app.mostrar_mensaje(f"Cliente registrado: {cliente.nombre}")
            messagebox.showinfo("Cliente", f"Cliente registrado: {cliente.nombre}")
        except Exception as exc:
            messagebox.showerror("Cliente", str(exc))

    def _etiqueta_stock_producto(self, producto: Producto) -> str:
        return f"{producto.codigo} - {producto.nombre} ({producto.categoria.title()})"

    def _actualizar_stock_catalogo(self) -> None:
        productos = sorted(self.tienda.productos, key=lambda producto: producto.nombre)
        self._stock_productos = {self._etiqueta_stock_producto(producto): producto for producto in productos}

        opciones = tuple(self._stock_productos.keys())
        if self._stock_combo_producto is not None:
            self._stock_combo_producto["values"] = opciones

        if not opciones:
            self._stock_producto_var.set("")
            self._stock_talla_var.set("")
            if self._stock_combo_talla is not None:
                self._stock_combo_talla["values"] = ()
            if self._stock_text is not None:
                _texto_ro(self._stock_text, self.app.texto_catalogo_operativo())
            return

        if self._stock_producto_var.get() not in self._stock_productos:
            self._stock_producto_var.set(opciones[0])

        self._actualizar_stock_tallas()
        if self._stock_text is not None:
            _texto_ro(self._stock_text, self.app.texto_catalogo_operativo())

    def _stock_producto_seleccionado(self) -> Producto | None:
        return self._stock_productos.get(self._stock_producto_var.get())

    def _actualizar_stock_tallas(self) -> None:
        producto = self._stock_producto_seleccionado()
        if self._stock_combo_talla is None:
            return
        if producto is None:
            self._stock_combo_talla["values"] = ()
            self._stock_talla_var.set("")
            return

        tallas = ordenar_tallas(producto.inventario)
        self._stock_combo_talla["values"] = tuple(tallas)
        if not tallas:
            self._stock_talla_var.set("")
        elif self._stock_talla_var.get() not in tallas:
            self._stock_talla_var.set(tallas[0])

    def _leer_cantidad_stock(self) -> int:
        try:
            cantidad = int(self._stock_cantidad_var.get().strip())
        except ValueError as exc:
            raise ValueError("La cantidad debe ser entera") from exc
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        return cantidad

    def _pasar_stock_a_tienda(self) -> None:
        try:
            producto = self._stock_producto_seleccionado()
            if producto is None:
                raise ValueError("Selecciona un producto")
            talla = self._stock_talla_var.get().strip().upper()
            if not talla:
                raise ValueError("Selecciona una talla")
            cantidad = self._leer_cantidad_stock()
            if producto.stock_bodega(talla) < cantidad:
                raise ValueError(
                    f"No hay suficiente stock en bodega para {producto.nombre} talla {talla}"
                )
            producto.mover_a_tienda(talla, cantidad)
            self.app.mostrar_mensaje(f"Stock movido a tienda: {producto.nombre} talla {talla}")
            messagebox.showinfo("Stock", f"Stock movido a tienda: {producto.nombre} talla {talla}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Stock", str(exc))

    def _recibir_stock_bodega(self) -> None:
        try:
            producto = self._stock_producto_seleccionado()
            if producto is None:
                raise ValueError("Selecciona un producto")
            talla = self._stock_talla_var.get().strip().upper()
            if not talla:
                raise ValueError("Selecciona una talla")
            cantidad = self._leer_cantidad_stock()
            producto.reponer_bodega(talla, cantidad)
            self.app.mostrar_mensaje(f"Stock recibido en bodega: {producto.nombre} talla {talla}")
            messagebox.showinfo("Stock", f"Stock recibido en bodega: {producto.nombre} talla {talla}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Stock", str(exc))

    def _leer_items(self) -> list[tuple[str, str, int]]:
        if self._items_text is None:
            raise RuntimeError("No se pudo leer el detalle de la venta")
        items: list[tuple[str, str, int]] = []
        for numero, linea in enumerate(self._items_text.get("1.0", tk.END).splitlines(), start=1):
            texto = linea.strip()
            if not texto:
                continue
            partes = texto.replace(",", " ").split()
            if len(partes) != 3:
                raise ValueError(f"Linea {numero}: usa 'codigo talla cantidad'")
            codigo, talla, cantidad_texto = partes
            try:
                cantidad = int(cantidad_texto)
            except ValueError as exc:
                raise ValueError(f"Linea {numero}: la cantidad debe ser entera") from exc
            items.append((codigo, talla, cantidad))
        if not items:
            raise ValueError("Debes registrar al menos un item")
        return items

    def _registrar_venta(self) -> None:
        try:
            documento = self._cliente_doc_var.get().strip()
            if not documento:
                raise ValueError("El documento del cliente es obligatorio")
            try:
                cliente = self.tienda.obtener_cliente(documento)
                self._cliente_nombre_var.set(cliente.nombre)
                self._cliente_tel_var.set(cliente.telefono)
                self._cliente_correo_var.set(cliente.correo)
            except KeyError:
                cliente = Cliente(
                    nombre=self._cliente_nombre_var.get(),
                    documento=documento,
                    telefono=self._cliente_tel_var.get(),
                    correo=self._cliente_correo_var.get(),
                )
            venta = self.tienda.registrar_venta(
                empleado_documento=self._empleado_doc_var.get(),
                cliente=cliente,
                items=self._leer_items(),
                metodo_pago=self._metodo_pago_var.get().strip() or "efectivo",
            )
            self.app.mostrar_mensaje(f"Venta registrada: {venta.id}")
            messagebox.showinfo("Venta", f"Venta registrada. Total: {formatear_moneda(venta.total)}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Venta", str(exc))


class PanelGerente(RolePanel):
    PASSWORD = "1234"

    def __init__(self, master: tk.Misc, app: "TiendaApp") -> None:
        super().__init__(master, app, "Panel de gerente", "Acceso total a empleados, gastos, inventario y caja.")
        self._nombre_empleado_var = tk.StringVar()
        self._documento_empleado_var = tk.StringVar()
        self._cargo_empleado_var = tk.StringVar(value="Vendedor")
        self._concepto_gasto_var = tk.StringVar()
        self._monto_gasto_var = tk.StringVar()
        self._categoria_gasto_var = tk.StringVar(value="general")
        self._responsable_gasto_var = tk.StringVar()
        self._empleados_text: ScrolledText | None = None
        self._gastos_text: ScrolledText | None = None
        self._reportes_text: ScrolledText | None = None
        self._inventario_text: ScrolledText | None = None

        controles = ttk.Frame(self._cuerpo)
        controles.grid(row=0, column=0, sticky="ew")
        ttk.Button(controles, text="Abrir tienda", command=self._abrir_tienda).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(controles, text="Cerrar tienda y salir", command=self._cerrar_tienda).grid(row=0, column=1, padx=6)

        notebook = ttk.Notebook(self._cuerpo)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        self._cuerpo.rowconfigure(1, weight=1)

        tab_empleados = ttk.Frame(notebook, padding=10)
        tab_gastos = ttk.Frame(notebook, padding=10)
        tab_reportes = ttk.Frame(notebook, padding=10)
        tab_inventario = ttk.Frame(notebook, padding=10)
        for tab in (tab_empleados, tab_gastos, tab_reportes, tab_inventario):
            tab.columnconfigure(0, weight=1)
        tab_empleados.rowconfigure(1, weight=1)
        tab_gastos.rowconfigure(1, weight=1)
        tab_reportes.rowconfigure(0, weight=1)
        tab_inventario.rowconfigure(0, weight=1)
        notebook.add(tab_empleados, text="Empleados")
        notebook.add(tab_gastos, text="Gastos")
        notebook.add(tab_reportes, text="Reportes")
        notebook.add(tab_inventario, text="Inventario")

        empleados = ttk.LabelFrame(tab_empleados, text="Registrar empleado", padding=10)
        empleados.grid(row=0, column=0, sticky="ew")
        empleados.columnconfigure(1, weight=1)
        _campo_formulario(empleados, 0, "Nombre", self._nombre_empleado_var, ancho=24)
        _campo_formulario(empleados, 1, "Documento", self._documento_empleado_var, ancho=24)
        _campo_formulario(empleados, 2, "Cargo", self._cargo_empleado_var, ancho=24)
        ttk.Button(empleados, text="Registrar empleado", command=self._registrar_empleado).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        lista_empleados = ttk.LabelFrame(tab_empleados, text="Empleados actuales", padding=10)
        lista_empleados.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        lista_empleados.columnconfigure(0, weight=1)
        lista_empleados.rowconfigure(1, weight=1)
        self._empleados_text = ScrolledText(lista_empleados, height=14, wrap="word", state="disabled")
        self._empleados_text.grid(row=1, column=0, sticky="nsew")

        gastos = ttk.LabelFrame(tab_gastos, text="Registrar gasto", padding=10)
        gastos.grid(row=0, column=0, sticky="ew")
        gastos.columnconfigure(1, weight=1)
        _campo_formulario(gastos, 0, "Concepto", self._concepto_gasto_var, ancho=28)
        _campo_formulario(gastos, 1, "Monto", self._monto_gasto_var, ancho=18)
        _campo_formulario(gastos, 2, "Categoria", self._categoria_gasto_var, ancho=18)
        _campo_formulario(gastos, 3, "Responsable", self._responsable_gasto_var, ancho=24)
        ttk.Button(gastos, text="Registrar gasto", command=self._registrar_gasto).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        lista_gastos = ttk.LabelFrame(tab_gastos, text="Gastos recientes", padding=10)
        lista_gastos.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        lista_gastos.columnconfigure(0, weight=1)
        lista_gastos.rowconfigure(0, weight=1)
        self._gastos_text = ScrolledText(lista_gastos, height=14, wrap="word", state="disabled")
        self._gastos_text.grid(row=0, column=0, sticky="nsew")

        reportes = ttk.LabelFrame(tab_reportes, text="Resumen de gerencia", padding=10)
        reportes.grid(row=0, column=0, sticky="nsew")
        reportes.columnconfigure(0, weight=1)
        reportes.rowconfigure(1, weight=1)
        self._reportes_text = ScrolledText(reportes, height=20, wrap="word", state="disabled")
        self._reportes_text.grid(row=1, column=0, sticky="nsew")

        inventario = ttk.LabelFrame(tab_inventario, text="Inventario completo", padding=10)
        inventario.grid(row=0, column=0, sticky="nsew")
        inventario.columnconfigure(0, weight=1)
        inventario.rowconfigure(1, weight=1)
        self._inventario_text = ScrolledText(inventario, height=20, wrap="word", state="disabled")
        self._inventario_text.grid(row=1, column=0, sticky="nsew")

    def refresh(self) -> None:
        if self._empleados_text is not None:
            _texto_ro(self._empleados_text, self.app.texto_empleados())
        if self._gastos_text is not None:
            _texto_ro(self._gastos_text, self.app.texto_gastos())
        if self._reportes_text is not None:
            _texto_ro(self._reportes_text, self.app.texto_reportes_gerencia())
        if self._inventario_text is not None:
            _texto_ro(self._inventario_text, self.app.texto_catalogo_operativo())

    def _registrar_empleado(self) -> None:
        try:
            empleado = Empleado(
                nombre=self._nombre_empleado_var.get(),
                documento=self._documento_empleado_var.get(),
                cargo=self._cargo_empleado_var.get(),
            )
            self.tienda.registrar_empleado(empleado)
            self.app.mostrar_mensaje(f"Empleado registrado: {empleado.nombre}")
            messagebox.showinfo("Empleado", f"Empleado registrado: {empleado.nombre}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Empleado", str(exc))

    def _registrar_gasto(self) -> None:
        try:
            gasto = self.tienda.registrar_gasto(
                concepto=self._concepto_gasto_var.get(),
                monto=self._monto_gasto_var.get(),
                categoria=self._categoria_gasto_var.get(),
                responsable=self._responsable_gasto_var.get(),
            )
            self.app.mostrar_mensaje(f"Gasto registrado: {gasto.concepto}")
            messagebox.showinfo("Gasto", f"Gasto registrado: {formatear_moneda(gasto.monto)}")
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Gasto", str(exc))

    def _abrir_tienda(self) -> None:
        if self.app.abrir_tienda("manual gerente"):
            messagebox.showinfo("Tienda", "La tienda fue abierta")
        else:
            messagebox.showinfo("Tienda", "La tienda ya estaba abierta")

    def _cerrar_tienda(self) -> None:
        if messagebox.askyesno("Cerrar tienda", "La tienda se cerrara y el panel visual se cerrara."):
            self.app.cerrar_tienda_y_salir("cerrado por gerente")


class TiendaApp:
    PASSWORD_GERENTE = "1234"
    TICK_MS = 1000

    def __init__(self, root: tk.Tk, tienda: Tienda, demo: dict[str, str] | None = None) -> None:
        self.root = root
        self.tienda = tienda
        self.demo = demo or {}
        self._segundos_sesion = 0
        self._cerrando = False
        self._panel_actual: ttk.Frame | None = None

        self._estado_var = tk.StringVar()
        self._rol_var = tk.StringVar(value="Rol: inicio")
        self._tiempo_var = tk.StringVar()
        self._mensaje_var = tk.StringVar(value="Selecciona cliente, empleado o gerente.")

        self.root.title(f"{self.tienda.nombre} - Acceso")
        self.root.geometry("1180x820")
        self.root.minsize(1100, 760)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._encabezado = ttk.Frame(self.root, padding=(12, 10, 12, 8))
        self._encabezado.grid(row=0, column=0, sticky="ew")
        self._encabezado.columnconfigure(0, weight=1)
        self._encabezado.columnconfigure(1, weight=1)

        ttk.Label(self._encabezado, text=self.tienda.nombre, font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self._encabezado, textvariable=self._estado_var).grid(row=0, column=1, sticky="e")
        ttk.Label(self._encabezado, textvariable=self._rol_var).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(self._encabezado, textvariable=self._tiempo_var).grid(row=1, column=1, sticky="e", pady=(4, 0))
        ttk.Label(self._encabezado, textvariable=self._mensaje_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        self._contenido = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        self._contenido.grid(row=1, column=0, sticky="nsew")
        self._contenido.columnconfigure(0, weight=1)
        self._contenido.rowconfigure(0, weight=1)

        self.mostrar_inicio()
        self._tick()

    def mostrar_mensaje(self, texto: str) -> None:
        self._mensaje_var.set(texto)

    def _actualizar_encabezado(self) -> None:
        estado = "abierta" if self.tienda.esta_abierta else "cerrada"
        self._estado_var.set(f"Tienda {estado}")
        self._tiempo_var.set(f"Tiempo de sesion: {_formatear_tiempo(self._segundos_sesion)}")

    def _cambiar_panel(self, panel: type[ttk.Frame]) -> ttk.Frame:
        if self._panel_actual is not None:
            self._panel_actual.destroy()
        self._panel_actual = panel(self._contenido, self)
        self._panel_actual.grid(row=0, column=0, sticky="nsew")
        if hasattr(self._panel_actual, "refresh"):
            getattr(self._panel_actual, "refresh")()
        return self._panel_actual

    def mostrar_inicio(self) -> None:
        self._rol_var.set("Rol: inicio")
        self.mostrar_mensaje("Selecciona cliente, empleado o gerente.")
        self._cambiar_panel(PantallaInicio)

    def mostrar_cliente(self) -> None:
        self._rol_var.set("Rol: cliente")
        self.mostrar_mensaje("Panel de cliente activo.")
        self._cambiar_panel(PanelCliente)

    def mostrar_empleado(self) -> None:
        self._rol_var.set("Rol: empleado")
        self.mostrar_mensaje("Panel de empleado activo.")
        self._cambiar_panel(PanelEmpleado)

    def mostrar_gerente(self) -> None:
        clave = simpledialog.askstring(
            "Acceso de gerente",
            "Ingresa la contraseña:",
            show="*",
            parent=self.root,
        )
        if clave is None:
            self.mostrar_mensaje("Acceso de gerente cancelado.")
            return
        if clave != self.PASSWORD_GERENTE:
            self.mostrar_mensaje("Contraseña de gerente incorrecta.")
            messagebox.showerror("Gerente", "Contraseña incorrecta")
            return
        self._rol_var.set("Rol: gerente")
        self.mostrar_mensaje("Panel de gerente activo.")
        self._cambiar_panel(PanelGerente)

    def abrir_tienda(self, motivo: str = "manual") -> bool:
        abrio = self.tienda.abrir_tienda(motivo)
        if abrio:
            self.mostrar_mensaje("La tienda fue abierta.")
        else:
            self.mostrar_mensaje("La tienda ya estaba abierta.")
        self._actualizar_encabezado()
        if self._panel_actual and hasattr(self._panel_actual, "refresh"):
            getattr(self._panel_actual, "refresh")()
        return abrio

    def cerrar_tienda_y_salir(self, motivo: str = "manual") -> None:
        if self._cerrando:
            return
        self._cerrando = True
        if self.tienda.esta_abierta:
            self.tienda.cerrar_tienda(motivo)
        self._actualizar_encabezado()
        self.mostrar_mensaje("La tienda se cerro. La interfaz se cerrara.")
        self.root.after(150, self.root.destroy)

    def cerrar_aplicacion(self) -> None:
        if self._cerrando:
            return
        self._cerrando = True
        self.root.destroy()

    def solicitar_metodo_pago(self) -> str | None:
        if self._cerrando:
            return None

        resultado: dict[str, str | None] = {"valor": None}
        ventana = tk.Toplevel(self.root)
        ventana.title("Metodo de pago")
        ventana.transient(self.root)
        ventana.resizable(False, False)
        ventana.grab_set()
        ventana.columnconfigure(0, weight=1)

        ttk.Label(ventana, text="Metodo de pago", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, padx=14, pady=(14, 4), sticky="w"
        )
        ttk.Label(ventana, text="Selecciona una forma de pago para continuar.").grid(
            row=1, column=0, padx=14, pady=(0, 12), sticky="w"
        )

        botones = ttk.Frame(ventana, padding=(14, 0, 14, 14))
        botones.grid(row=2, column=0, sticky="ew")

        def elegir(valor: str) -> None:
            resultado["valor"] = valor
            ventana.destroy()

        for indice, (texto, valor) in enumerate(
            (("Efectivo", "efectivo"), ("Tarjeta", "tarjeta"), ("Transferencia", "transferencia"))
        ):
            ttk.Button(botones, text=texto, command=lambda v=valor: elegir(v)).grid(
                row=0, column=indice, padx=4, sticky="ew"
            )
            botones.columnconfigure(indice, weight=1)

        def _cerrar() -> None:
            ventana.destroy()

        ventana.protocol("WM_DELETE_WINDOW", _cerrar)
        try:
            self.root.wait_window(ventana)
        except tk.TclError:
            return None
        return resultado["valor"]

    def texto_catalogo_publico(self) -> str:
        categorias_base = ["camisas", "pantalones", "zapatos"]
        categorias = [categoria for categoria in categorias_base if categoria in self.tienda.categorias_disponibles()]
        for categoria in self.tienda.categorias_disponibles():
            if categoria not in categorias:
                categorias.append(categoria)

        if not categorias:
            return "No hay productos registrados."

        lineas: list[str] = []
        for categoria in categorias:
            productos = self.tienda.productos_por_categoria(categoria)
            if not productos:
                continue
            lineas.append(f"{categoria.title()}:")
            for producto in productos:
                tallas = []
                for talla in ordenar_tallas(producto.inventario):
                    inventario = producto.inventario[talla]
                    if inventario.tienda > 0 or inventario.bodega > 0:
                        tallas.append(f"{talla} (tienda {inventario.tienda}, bodega {inventario.bodega})")
                disponibles = ", ".join(tallas) if tallas else "sin inventario"
                lineas.append(
                    f"  {producto.codigo} | {producto.nombre} | {formatear_moneda(producto.precio_venta)} | {disponibles}"
                )
            lineas.append("")
        return "\n".join(lineas).strip()

    def texto_catalogo_categoria(self, categoria: str) -> str:
        productos = self.tienda.productos_por_categoria(categoria)
        titulo = categoria.strip().title() or "Catalogo"
        if not productos:
            return f"No hay productos en {titulo}."

        lineas: list[str] = [f"{titulo}:"]
        for producto in productos:
            lineas.append(f"{producto.codigo} | {producto.nombre} | {formatear_moneda(producto.precio_venta)}")
            for talla in ordenar_tallas(producto.inventario):
                inventario = producto.inventario[talla]
                lineas.append(
                    f"  - talla {talla}: tienda {inventario.tienda}, bodega {inventario.bodega}"
                )
        return "\n".join(lineas)

    def texto_catalogo_operativo(self) -> str:
        productos = sorted(self.tienda.productos, key=lambda producto: producto.nombre)
        if not productos:
            return "No hay productos registrados."
        return "\n\n".join(producto.resumen_inventario() for producto in productos)

    def texto_empleados(self) -> str:
        empleados = sorted(self.tienda.empleados, key=lambda empleado: empleado.nombre)
        if not empleados:
            return "No hay empleados registrados."
        return "\n".join(f"- {empleado.resumen()}" for empleado in empleados)

    def texto_gastos(self) -> str:
        gastos = sorted(self.tienda.gastos, key=lambda gasto: gasto.fecha, reverse=True)
        if not gastos:
            return "No hay gastos registrados."
        lineas = []
        for gasto in gastos[:15]:
            lineas.append(
                f"- {gasto.fecha:%Y-%m-%d %H:%M} | {gasto.concepto} | {gasto.categoria} | "
                f"{formatear_moneda(gasto.monto)} | {gasto.responsable or 'sin responsable'}"
            )
        return "\n".join(lineas)

    def texto_reportes_gerencia(self) -> str:
        ventas_por_empleado = self.tienda.ventas_por_empleado()
        ventas_recientes = sorted(self.tienda.ventas, key=lambda venta: venta.fecha, reverse=True)

        lineas = [
            self.tienda.resumen_operativo(),
            "",
            f"Total ventas: {formatear_moneda(self.tienda.total_ventas)}",
            f"Costo mercancia: {formatear_moneda(self.tienda.costo_mercancia)}",
            f"Gastos: {formatear_moneda(self.tienda.total_gastos)}",
            f"Ganancia bruta: {formatear_moneda(self.tienda.ganancia_bruta)}",
            f"Ganancia neta: {formatear_moneda(self.tienda.ganancia_neta)}",
            "",
            "Ventas por empleado:",
        ]
        if ventas_por_empleado:
            for empleado, total in sorted(ventas_por_empleado.items()):
                lineas.append(f"- {empleado}: {formatear_moneda(total)}")
        else:
            lineas.append("- sin ventas")

        lineas.extend(["", "Ultimas ventas:"])
        if ventas_recientes:
            for venta in ventas_recientes[:10]:
                lineas.append(f"- {venta.resumen()}")
        else:
            lineas.append("- sin ventas")
        return "\n".join(lineas)

    def _tick(self) -> None:
        if self._cerrando:
            return
        self._segundos_sesion += 1
        self._actualizar_encabezado()
        self.root.after(self.TICK_MS, self._tick)


from tienda import *  


def main() -> None:
    tienda, demo = construir_tienda_demo()
    root = tk.Tk()
    TiendaApp(root, tienda, demo)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except tk.TclError as exc:
        raise SystemExit(f"No se pudo abrir la interfaz grafica: {exc}")
