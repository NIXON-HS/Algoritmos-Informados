"""
==============================================================================
MÓDULO: puzzle_view.py
PROPÓSITO: Componente visual interactivo para el tablero del 8-Puzzle (3x3).
           Renderiza las fichas con números, detecta clics manuales del usuario,
           resalta fichas que se encuentran en su posición meta en verde
           y actualiza el estado dinámicamente durante la animación.
==============================================================================
"""

import tkinter as tk
from typing import Optional, Callable
from logic.puzzle_state import PuzzleState, DEFAULT_GOAL


class PuzzleView(tk.Frame):
    """
    Widget de Tkinter para representar gráficamente el tablero del 8-Puzzle 3x3.
    """

    def __init__(
        self,
        master,
        state: Optional[PuzzleState] = None,
        goal_state: Optional[PuzzleState] = None,
        size: int = 260,
        on_state_change: Optional[Callable[[PuzzleState], None]] = None,
        **kwargs
    ):
        """
        :param master: Contenedor padre de Tkinter.
        :param state: Estado inicial del puzzle a mostrar.
        :param goal_state: Estado meta de referencia para resaltar fichas correctas.
        :param size: Dimensión en píxeles (ancho y alto) del tablero cuadrado.
        :param on_state_change: Callback invocado cuando el usuario mueve una ficha manualmente.
        """
        super().__init__(master, bg="#ffffff", **kwargs)

        self.size = size
        self.tile_size = (size - 16) // 3
        self.padding = 8

        self.state = state if state else PuzzleState(DEFAULT_GOAL)
        self.goal_state = goal_state if goal_state else PuzzleState(DEFAULT_GOAL)
        self.on_state_change = on_state_change
        self.is_interactive = True

        # Paleta de colores moderna
        self.bg_board = "#e2e8f0"        # Fondo de la cuadrícula
        self.tile_bg = "#3b82f6"         # Azul para fichas fuera de posición meta
        self.tile_correct_bg = "#10b981" # Verde esmeralda para fichas en su posición meta
        self.tile_text_color = "#ffffff" # Color blanco del texto
        self.blank_bg = "#f8fafc"        # Fondo claro para el espacio en blanco (0)
        self.border_color = "#cbd5e1"

        # Canvas para el renderizado del tablero
        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            bg=self.bg_board,
            highlightthickness=2,
            highlightbackground="#cbd5e1"
        )
        self.canvas.pack(padx=2, pady=2)

        # Vincular evento de clic del ratón
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Dibujar estado inicial
        self.draw()

    def set_state(self, state: PuzzleState):
        """
        Actualiza el estado actual del puzzle y redibuja el tablero en pantalla.
        """
        self.state = state
        self.draw()

    def set_goal(self, goal_state: PuzzleState):
        """
        Actualiza el estado objetivo de referencia y redibuja.
        """
        self.goal_state = goal_state
        self.draw()

    def set_interactive(self, enable: bool):
        """
        Habilita o deshabilita los clics manuales del usuario sobre el tablero.
        """
        self.is_interactive = enable

    def _on_canvas_click(self, event):
        """
        Detecta en qué casilla hizo clic el usuario y mueve la ficha si es adyacente al espacio blanco.
        """
        if not self.is_interactive:
            return

        col = (event.x - self.padding) // self.tile_size
        row = (event.y - self.padding) // self.tile_size

        # Validar que el clic ocurrió dentro de la cuadrícula de 3x3
        if 0 <= row < 3 and 0 <= col < 3:
            index = row * 3 + col
            result = self.state.move_tile_at_index(index)
            if result is not None:
                _, new_state = result
                self.state = new_state
                self.draw()
                # Notificar a la aplicación principal para actualizar métricas
                if self.on_state_change:
                    self.on_state_change(self.state)

    def draw(self):
        """
        Dibuja todas las casillas del tablero 3x3, aplicando sombras,
        colores dinámicos (verde si la ficha está en la meta) y tipografía nítida.
        """
        self.canvas.delete("all")

        # Dibujar marco y fondo del tablero
        self.canvas.create_rectangle(
            2, 2, self.size - 2, self.size - 2,
            fill=self.bg_board, outline="#94a3b8", width=1
        )

        # Dibujar cada una de las 9 casillas
        for idx, val in enumerate(self.state.tiles):
            r, c = idx // 3, idx % 3
            x1 = self.padding + c * self.tile_size + 2
            y1 = self.padding + r * self.tile_size + 2
            x2 = x1 + self.tile_size - 4
            y2 = y1 + self.tile_size - 4

            if val == 0:
                # Espacio en blanco (casilla vacía)
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=self.blank_bg,
                    outline="#cbd5e1",
                    width=1
                )
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text="·",
                    font=("Segoe UI", 18, "bold"),
                    fill="#94a3b8"
                )
            else:
                # Comprobar si la ficha ya se encuentra en su posición meta
                is_in_goal = False
                if self.goal_state and idx < len(self.goal_state.tiles):
                    is_in_goal = (self.goal_state.tiles[idx] == val)

                fill_color = self.tile_correct_bg if is_in_goal else self.tile_bg

                # Sombra inferior derecha de la ficha
                self.canvas.create_rectangle(
                    x1 + 2, y1 + 2, x2 + 2, y2 + 2,
                    fill="#94a3b8",
                    outline=""
                )
                # Cuerpo de la ficha
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill_color,
                    outline="#ffffff",
                    width=1.5
                )
                # Número de la ficha
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=str(val),
                    font=("Segoe UI", 22, "bold"),
                    fill=self.tile_text_color
                )
