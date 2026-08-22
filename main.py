"""
==============================================================================
ARCHIVO: main.py
PROPÓSITO: Punto de entrada principal para ejecutar la aplicación de 8-Puzzle
           con Algoritmos de Búsqueda Informada (Búsqueda Voraz y Búsqueda A*).
==============================================================================
"""

import sys
from gui.app import App


def main():
    """
    Función principal que instancia la aplicación gráfica e inicia el bucle de eventos.
    """
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
