"""
==============================================================================
MÓDULO: app.py
PROPÓSITO: Ventana principal de la aplicación gráfica del 8-Puzzle.
           Integra la selección de algoritmos (Voraz y A*), el tablero interactivo,
           la animación fluida de la solución y la visualización del árbol de búsqueda.
==============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, List

from logic.puzzle_state import PuzzleState, DEFAULT_GOAL, DEFAULT_INITIAL, PRESET_STATES
from logic.node import Node
from logic.search_algorithms import (
    greedy_best_first_search,
    a_star_search,
    SearchResult
)
from gui.puzzle_view import PuzzleView
from gui.tree_view import TreeView


class App(tk.Tk):
    """
    Clase principal que hereda de tk.Tk y gestiona el ciclo de vida de la aplicación.
    """

    def __init__(self):
        """Inicializa la ventana principal, modelos de estado y la interfaz de usuario."""
        super().__init__()
        self.title("8-Puzzle - Algoritmos de Búsqueda Informada (Heurística de Manhattan)")
        self.geometry("1400x900")
        self.minsize(1150, 750)
        self.configure(bg="#f1f5f9")

        # =====================================================================
        # MODELO DE ESTADOS DEL PUZZLE
        # =====================================================================
        self.goal_state: PuzzleState = PuzzleState(DEFAULT_GOAL)
        self.initial_state: PuzzleState = PuzzleState(DEFAULT_INITIAL)
        self.current_state: PuzzleState = self.initial_state

        # =====================================================================
        # RESULTADOS Y CONTROL DE ANIMACIÓN
        # =====================================================================
        self.search_result: Optional[SearchResult] = None
        self._anim_timer: Optional[str] = None  # Identificador del callback after() de Tkinter

        # =====================================================================
        # VARIABLES DE CONTROL DE LA INTERFAZ
        # =====================================================================
        self.var_algorithm = tk.StringVar(value="a_star")

        self._setup_styles()
        self._build_ui()
        self._update_state_metrics()

    def _setup_styles(self):
        """Configura los estilos visuales de ttk con temática clara moderna."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#ffffff")
        style.configure("TLabelframe", background="#ffffff")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), background="#ffffff", foreground="#1e293b")

    def _build_ui(self):
        """Construye la distribución de la interfaz gráfica dividida en dos paneles."""
        # Contenedor principal horizontal
        main_container = tk.Frame(self, bg="#f1f5f9")
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # =====================================================================
        # PANEL IZQUIERDO: Configuración, Tablero 8-Puzzle, Ejecución y Métricas
        # =====================================================================
        sidebar_frame = tk.Frame(main_container, bg="#f1f5f9", width=420)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar_frame.pack_propagate(False)

        # Canvas con scrollbar para asegurar que la barra lateral quepa en pantallas pequeñas
        sidebar_canvas = tk.Canvas(sidebar_frame, bg="#ffffff", bd=1, relief=tk.SOLID, highlightbackground="#cbd5e1")
        sidebar_scrollbar = ttk.Scrollbar(sidebar_frame, orient=tk.VERTICAL, command=sidebar_canvas.yview)
        
        self.sidebar_content = tk.Frame(sidebar_canvas, bg="#ffffff", padx=16, pady=14)
        self.sidebar_content.bind(
            "<Configure>",
            lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
        )

        sidebar_canvas.create_window((0, 0), window=self.sidebar_content, anchor="nw", width=400)
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. TÍTULO Y ENCABEZADO
        lbl_title = tk.Label(
            self.sidebar_content,
            text="8-Puzzle: Búsqueda Informada",
            bg="#ffffff",
            fg="#0f172a",
            font=("Segoe UI", 15, "bold")
        )
        lbl_title.pack(anchor=tk.W)

        lbl_sub = tk.Label(
            self.sidebar_content,
            text="Heurística: Distancia de Manhattan",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 9)
        )
        lbl_sub.pack(anchor=tk.W, pady=(0, 10))

        # 2. SELECCIÓN DE ALGORITMO
        group_algo = tk.LabelFrame(
            self.sidebar_content,
            text="1. Algoritmo de Búsqueda",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID
        )
        group_algo.pack(fill=tk.X, pady=(0, 10))

        rb_voraz = tk.Radiobutton(
            group_algo,
            text="Búsqueda Voraz Primero el Mejor  [ f(n) = h(n) ]",
            variable=self.var_algorithm,
            value="greedy",
            bg="#ffffff",
            fg="#0f172a",
            activebackground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            command=self._on_algorithm_change
        )
        rb_voraz.pack(anchor=tk.W, pady=2)

        rb_astar = tk.Radiobutton(
            group_algo,
            text="Búsqueda A* (A-Estrella)  [ f(n) = g(n) + h(n) ]",
            variable=self.var_algorithm,
            value="a_star",
            bg="#ffffff",
            fg="#0f172a",
            activebackground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            command=self._on_algorithm_change
        )
        rb_astar.pack(anchor=tk.W, pady=2)

        self.lbl_algo_desc = tk.Label(
            group_algo,
            text="• A* garantiza el camino óptimo sumando costo real g(n) y heurística h(n).",
            bg="#f8fafc",
            fg="#475569",
            font=("Segoe UI", 8, "italic"),
            padx=6,
            pady=4,
            wraplength=360,
            justify=tk.LEFT
        )
        self.lbl_algo_desc.pack(fill=tk.X, pady=(4, 0))

        # 3. TABLERO 8-PUZZLE INTERACTIVO
        group_puzzle = tk.LabelFrame(
            self.sidebar_content,
            text="2. Tablero 8-Puzzle",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID
        )
        group_puzzle.pack(fill=tk.X, pady=(0, 10))

        board_container = tk.Frame(group_puzzle, bg="#ffffff")
        board_container.pack(pady=4)

        self.puzzle_view = PuzzleView(
            board_container,
            state=self.current_state,
            goal_state=self.goal_state,
            size=220,
            on_state_change=self._on_manual_tile_move
        )
        self.puzzle_view.pack()

        # Botones de configuración del tablero
        lbl_hint = tk.Label(
            group_puzzle,
            text="💡 Mueve fichas con clic o usa los controles:",
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#64748b"
        )
        lbl_hint.pack(anchor=tk.W, pady=(4, 2))

        btn_box1 = tk.Frame(group_puzzle, bg="#ffffff")
        btn_box1.pack(fill=tk.X, pady=(2, 2))

        btn_shuffle = tk.Button(
            btn_box1, text="🎲 Revolver", font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9", fg="#1e293b", activebackground="#e2e8f0",
            relief=tk.SOLID, bd=1, padx=6, pady=3, cursor="hand2",
            command=self._shuffle_board
        )
        btn_shuffle.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        btn_custom = tk.Button(
            btn_box1, text="✏️ Ingresar...", font=("Segoe UI", 9, "bold"),
            bg="#f8fafc", fg="#475569", activebackground="#e2e8f0",
            relief=tk.SOLID, bd=1, padx=6, pady=3, cursor="hand2",
            command=self._prompt_custom_state
        )
        btn_custom.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        btn_reset_goal = tk.Button(
            btn_box1, text="🎯 Meta", font=("Segoe UI", 9, "bold"),
            bg="#f8fafc", fg="#475569", activebackground="#e2e8f0",
            relief=tk.SOLID, bd=1, padx=6, pady=3, cursor="hand2",
            command=self._reset_to_goal
        )
        btn_reset_goal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # 4. EJECUCIÓN DEL ALGORITMO
        group_controls = tk.LabelFrame(
            self.sidebar_content,
            text="3. Ejecución del Algoritmo",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID
        )
        group_controls.pack(fill=tk.X, pady=(0, 10))

        self.btn_solve = tk.Button(
            group_controls,
            text="⚡ Resolver con A*",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            pady=8,
            cursor="hand2",
            command=self._execute_search
        )
        self.btn_solve.pack(fill=tk.X, pady=2)

        # 5. PANEL DE MÉTRICAS EN VIVO
        group_metrics = tk.LabelFrame(
            self.sidebar_content,
            text="4. Métricas de Evaluación",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID
        )
        group_metrics.pack(fill=tk.X, pady=(0, 10))

        # Tarjetas compactas con valores de h(n), g(n) y f(n)
        metrics_grid = tk.Frame(group_metrics, bg="#ffffff")
        metrics_grid.pack(fill=tk.X)

        self._create_metric_card(metrics_grid, "Heurística h(n)", "0", 0, 0, "#0284c7")
        self._create_metric_card(metrics_grid, "Costo g(n)", "0", 0, 1, "#6366f1")
        self._create_metric_card(metrics_grid, "Evaluación f(n)", "0", 0, 2, "#059669")

        self.lbl_metric_expanded = self._create_metric_row(group_metrics, "Nodos Expandidos:", "-")
        self.lbl_metric_generated = self._create_metric_row(group_metrics, "Nodos Generados:", "-")
        self.lbl_metric_frontier = self._create_metric_row(group_metrics, "Frontera Máxima:", "-")
        self.lbl_metric_cost = self._create_metric_row(group_metrics, "Longitud Solución:", "-")
        self.lbl_metric_time = self._create_metric_row(group_metrics, "Tiempo de Búsqueda:", "-")

        # =====================================================================
        # PANEL DERECHO: Visualización del Árbol de Búsqueda
        # =====================================================================
        right_panel = tk.Frame(main_container, bg="#ffffff", bd=1, relief=tk.SOLID, highlightbackground="#cbd5e1")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Header del árbol con título y leyenda de colores
        tree_header = tk.Frame(right_panel, bg="#ffffff", padx=12, pady=8, bd=1, relief=tk.FLAT)
        tree_header.pack(fill=tk.X)

        lbl_tree_title = tk.Label(
            tree_header,
            text="Árbol de Búsqueda",
            font=("Segoe UI", 13, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        lbl_tree_title.pack(side=tk.LEFT)

        # Leyenda de estados de los nodos
        legend_frame = tk.Frame(tree_header, bg="#ffffff")
        legend_frame.pack(side=tk.RIGHT, padx=6)

        self._create_legend_item(legend_frame, "#ede9fe", "#7c3aed", "Raíz")
        self._create_legend_item(legend_frame, "#d1fae5", "#059669", "Solución")
        self._create_legend_item(legend_frame, "#e0f2fe", "#0284c7", "Explorado")
        self._create_legend_item(legend_frame, "#f8fafc", "#94a3b8", "Frontera")
        self._create_legend_item(legend_frame, "#fef08a", "#ca8a04", "Seleccionado")

        # Visualizador interactivo del árbol
        self.tree_view = TreeView(
            right_panel,
            on_node_click=self._on_tree_node_clicked
        )
        self.tree_view.pack(fill=tk.BOTH, expand=True)

    def _create_metric_card(self, parent, label: str, value: str, row: int, col: int, color: str):
        """Crea una tarjeta métrica con valor grande y etiqueta explicativa."""
        card = tk.Frame(parent, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=4, pady=4, highlightbackground="#e2e8f0")
        card.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
        parent.grid_columnconfigure(col, weight=1)

        lbl_val = tk.Label(card, text=value, font=("Segoe UI", 12, "bold"), fg=color, bg="#f8fafc")
        lbl_val.pack()
        lbl_text = tk.Label(card, text=label, font=("Segoe UI", 7), fg="#64748b", bg="#f8fafc")
        lbl_text.pack()

        if "h(n)" in label:
            self.lbl_card_h = lbl_val
        elif "g(n)" in label:
            self.lbl_card_g = lbl_val
        elif "f(n)" in label:
            self.lbl_card_f = lbl_val

    def _create_metric_row(self, parent, label_text: str, default_val: str) -> tk.Label:
        """Crea una fila de métrica con título a la izquierda y valor a la derecha."""
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill=tk.X, pady=1)

        lbl_title = tk.Label(row, text=label_text, font=("Segoe UI", 8), fg="#475569", bg="#ffffff")
        lbl_title.pack(side=tk.LEFT)

        lbl_val = tk.Label(row, text=default_val, font=("Segoe UI", 8, "bold"), fg="#0f172a", bg="#ffffff")
        lbl_val.pack(side=tk.RIGHT)
        return lbl_val

    def _create_legend_item(self, parent, bg_col: str, border_col: str, text: str):
        """Crea un indicador con muestra de color para la leyenda del árbol."""
        item = tk.Frame(parent, bg="#ffffff")
        item.pack(side=tk.LEFT, padx=5)

        box = tk.Frame(item, width=14, height=14, bg=bg_col, bd=1, relief=tk.SOLID, highlightbackground=border_col)
        box.pack(side=tk.LEFT, padx=(0, 3))
        box.pack_propagate(False)

        lbl = tk.Label(item, text=text, font=("Segoe UI", 8), bg="#ffffff", fg="#475569")
        lbl.pack(side=tk.LEFT)

    def _on_algorithm_change(self):
        """Actualiza el texto del botón y la descripción al cambiar de algoritmo."""
        algo = self.var_algorithm.get()
        if algo == "a_star":
            self.btn_solve.configure(text="⚡ Resolver con A*")
            self.lbl_algo_desc.configure(
                text="• A* garantiza el camino óptimo sumando costo acumulado g(n) y heurística h(n)."
            )
        else:
            self.btn_solve.configure(text="⚡ Resolver con Voraz")
            self.lbl_algo_desc.configure(
                text="• Voraz se guía exclusivamente por la heurística f(n) = h(n). Rápido pero no siempre óptimo."
            )

    def _cancel_animation(self):
        """Cancela de forma segura cualquier animación en curso."""
        if self._anim_timer is not None:
            try:
                self.after_cancel(self._anim_timer)
            except Exception:
                pass
            self._anim_timer = None

    def _on_manual_tile_move(self, new_state: PuzzleState):
        """Maneja el movimiento manual de una ficha en el tablero por clic."""
        self._cancel_animation()
        self.current_state = new_state
        self.initial_state = new_state
        self._reset_search_state()
        self._update_state_metrics()

    def _shuffle_board(self):
        """Revuelve el tablero generando una configuración aleatoria matemáticamente resoluble."""
        self._cancel_animation()
        self.initial_state = PuzzleState.create_random_solvable(self.goal_state)
        self.current_state = self.initial_state
        self.puzzle_view.set_state(self.current_state)
        self._reset_search_state()
        self._update_state_metrics()

    def _reset_to_goal(self):
        """Restablece el tablero directamente al estado objetivo."""
        self._cancel_animation()
        self.initial_state = self.goal_state
        self.current_state = self.initial_state
        self.puzzle_view.set_state(self.current_state)
        self._reset_search_state()
        self._update_state_metrics()

    def _prompt_custom_state(self):
        """Abre un cuadro de diálogo para que el usuario ingrese una permutación personalizada."""
        self._cancel_animation()
        curr_str = " ".join(str(x) for x in self.current_state.tiles)
        val = simpledialog.askstring(
            "Ingresar Estado Personalizado",
            "Ingrese 9 números del 0 al 8 separados por espacio\n(ejemplo: 1 2 3 4 5 6 7 8 0):",
            initialvalue=curr_str,
            parent=self
        )
        if not val:
            return

        try:
            nums = tuple(int(x.strip()) for x in val.replace(",", " ").split())
            new_state = PuzzleState(nums)
            if not new_state.is_solvable(self.goal_state):
                resp = messagebox.askyesno(
                    "Estado No Resoluble",
                    "La configuración ingresada tiene distinta paridad de inversiones y NO es resoluble hacia el objetivo.\n\n¿Desea mantenerla de todos modos?",
                    parent=self
                )
                if not resp:
                    return

            self.initial_state = new_state
            self.current_state = self.initial_state
            self.puzzle_view.set_state(self.current_state)
            self._reset_search_state()
            self._update_state_metrics()
        except Exception as e:
            messagebox.showerror("Error de Formato", f"Entrada inválida: {e}", parent=self)

    def _reset_search_state(self):
        """Limpia el resultado y métricas de la búsqueda previa."""
        self._cancel_animation()
        self.search_result = None
        self.tree_view.set_tree(None)
        self.lbl_metric_expanded.configure(text="-")
        self.lbl_metric_generated.configure(text="-")
        self.lbl_metric_frontier.configure(text="-")
        self.lbl_metric_cost.configure(text="-")
        self.lbl_metric_time.configure(text="-")

    def _update_state_metrics(self, node: Optional[Node] = None):
        """Actualiza los valores mostrados en las tarjetas de h(n), g(n) y f(n)."""
        h_val = self.current_state.manhattan_distance(self.goal_state)
        g_val = node.g if node else 0
        if self.var_algorithm.get() == "a_star":
            f_val = g_val + h_val
        else:
            f_val = h_val

        self.lbl_card_h.configure(text=str(h_val))
        self.lbl_card_g.configure(text=str(g_val))
        self.lbl_card_f.configure(text=str(f_val))

    def _execute_search(self):
        """Ejecuta el algoritmo seleccionado y lanza la animación automática del camino solución."""
        self._cancel_animation()
        algo = self.var_algorithm.get()

        # Validación matemática de solubilidad
        if not self.initial_state.is_solvable(self.goal_state):
            messagebox.showwarning(
                "Estado Insoluble",
                "El estado inicial no tiene solución matemática hacia el objetivo debido a la paridad de inversiones.",
                parent=self
            )
            return

        # Deshabilitar botón temporalmente durante el cómputo
        self.btn_solve.configure(state=tk.DISABLED, text="Buscando...")
        self.update_idletasks()

        if algo == "greedy":
            result = greedy_best_first_search(self.initial_state, self.goal_state)
        else:
            result = a_star_search(self.initial_state, self.goal_state)

        self.search_result = result
        self.btn_solve.configure(
            state=tk.NORMAL,
            text="⚡ Resolver con " + ("A*" if algo == "a_star" else "Voraz")
        )

        if not result.success:
            messagebox.showwarning("Sin Solución", result.message, parent=self)
            return

        # Actualizar métricas globales
        self.lbl_metric_expanded.configure(text=f"{result.expanded_count:,}")
        self.lbl_metric_generated.configure(text=f"{result.generated_count:,}")
        self.lbl_metric_frontier.configure(text=f"{result.max_frontier_size:,}")
        self.lbl_metric_cost.configure(text=f"{result.solution_cost} pasos")
        self.lbl_metric_time.configure(text=f"{result.execution_time_ms:.2f} ms")

        # Cargar el árbol visual completo en el panel derecho
        self.tree_view.set_tree(result.root_node)

        # Iniciar la animación fluida paso a paso sobre el tablero
        if result.solution_path:
            self._animate_solution(result.solution_path, 0)

    def _animate_solution(self, path: List[Node], step_idx: int = 0):
        """
        Reproduce secuencialmente cada paso de la solución sobre el tablero
        y resalta el nodo correspondiente en el árbol de búsqueda.
        """
        if not path or step_idx >= len(path):
            self._anim_timer = None
            return

        node = path[step_idx]
        self.current_state = node.state
        self.puzzle_view.set_state(self.current_state)

        # Sincronizar selección en el árbol
        self.tree_view.selected_node = node
        self.tree_view.redraw()
        self._update_state_metrics(node)

        # Programar siguiente paso de la animación
        if step_idx + 1 < len(path):
            self._anim_timer = self.after(350, lambda: self._animate_solution(path, step_idx + 1))
        else:
            self._anim_timer = None

    def _on_tree_node_clicked(self, node: Node):
        """
        Sincroniza el tablero del puzzle con el estado del nodo seleccionado al hacer clic en el árbol.
        """
        self._cancel_animation()
        self.current_state = node.state
        self.puzzle_view.set_state(self.current_state)
        self._update_state_metrics(node)
