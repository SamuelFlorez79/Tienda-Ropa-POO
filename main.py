import tkinter as tk

from logica.tienda import Tienda
from interfaz.interfaz_tienda import _LegacyTiendaApp


def main():
    root = tk.Tk()

    tienda = Tienda()

    app = _LegacyTiendaApp(root, tienda)

    root.mainloop()


if __name__ == "__main__":
    main()
