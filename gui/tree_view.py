"""
==============================================================================
MÓDULO: tree_view.py
PROPÓSITO: Componente visual interactivo y ultra-optimizado para el árbol de búsqueda.
           Implementa Viewport Frustum Culling (recorte de vista), cálculo de layout
           jerárquico, sombras suaves, mini-tableros coloreados, aristas con curvas
           Bézier, badges de movimiento y navegación fluida con Zoom y Pan.
==============================================================================
"""

import tkinter as tk
from typing import Optional, Dict, Tuple, Set, List, Callable
from logic.node import Node
from logic.puzzle_state import PuzzleState, DEFAULT_GOAL


class TreeView(tk.Frame):
    """
    Canvas interactivo para renderizar el árbol de búsqueda jerárquico.
    Utiliza técnicas de recorte de vista (Culling) para renderizar a 60 FPS incluso con miles de nodos.
    """

    def __init__(self, master, on_node_click: Optional[Callable[[Node], None]] = None, **kwargs):
        """
        :param master: Widget contenedor padre.
        :param on_node_click: Callback ejecutado cuando el usuario hace clic sobre un nodo del árbol.
        """
        super().__init__(master, bg="#f8fafc", **kwargs)

        self.on_node_click = on_node_click

        # Canvas principal sin borde grueso para estética plana moderna
        self.canvas = tk.Canvas(
            self,
            bg="#f8fafc",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Variables de control de cámara (Transformada de Vista: Zoom y Pan)
        self.zoom_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.start_drag_x = 0
        self.start_drag_y = 0

        # Estructuras de datos del árbol en memoria
        self.root_node: Optional[Node] = None
        self.selected_node: Optional[Node] = None
        self.node_positions: Dict[int, Tuple[float, float]] = {}              # id -> (x_centro, y_centro)
        self.subtree_bboxes: Dict[int, Tuple[float, float, float, float]] = {}  # id -> (min_x, min_y, max_x, max_y)
        self.node_map: Dict[int, Node] = {}                                     # id -> instancia Node
        self.node_boxes: Dict[int, Tuple[float, float, float, float]] = {}      # id -> bounding box en espacio mundo

        # Dimensiones de las tarjetas de nodos
        self.node_width = 144.0
        self.node_height = 88.0
        self.level_gap_y = 140.0
        self.node_gap_x = 28.0

        # Eventos de interacción del ratón
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.15, e.x, e.y))  # Linux Scroll Up
        self.canvas.bind("<Button-5>", lambda e: self._zoom(0.85, e.x, e.y))  # Linux Scroll Down
        self.canvas.bind("<Configure>", lambda e: self._on_resize())

        self._has_dragged = False
        self._create_controls()

    def _create_controls(self):
        """
        Crea la barra flotante de herramientas en la esquina superior derecha del canvas
        con botones de zoom in (+), zoom out (-) y ajuste a pantalla completa.
        """
        toolbar = tk.Frame(
            self.canvas,
            bg="#ffffff",
            bd=1,
            relief=tk.SOLID,
            highlightbackground="#cbd5e1",
            highlightthickness=1
        )
        toolbar.place(relx=0.98, rely=0.02, anchor=tk.NE)

        btn_plus = tk.Button(
            toolbar, text="＋", font=("Segoe UI", 11, "bold"),
            bg="#ffffff", fg="#334155", activebackground="#f1f5f9",
            relief=tk.FLAT, width=3, pady=2, command=lambda: self._zoom(1.25), cursor="hand2"
        )
        btn_plus.pack(side=tk.LEFT, padx=1, pady=1)

        btn_minus = tk.Button(
            toolbar, text="－", font=("Segoe UI", 11, "bold"),
            bg="#ffffff", fg="#334155", activebackground="#f1f5f9",
            relief=tk.FLAT, width=3, pady=2, command=lambda: self._zoom(0.8), cursor="hand2"
        )
        btn_minus.pack(side=tk.LEFT, padx=1, pady=1)

        sep = tk.Frame(toolbar, width=1, bg="#e2e8f0", height=22)
        sep.pack(side=tk.LEFT, padx=2)

        btn_fit = tk.Button(
            toolbar, text="🔍 Ajustar Vista", font=("Segoe UI", 9, "bold"),
            bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff",
            relief=tk.FLAT, padx=10, pady=4, command=self.fit_to_view, cursor="hand2"
        )
        btn_fit.pack(side=tk.LEFT, padx=2, pady=1)

    def set_tree(self, root_node: Optional[Node]):
        """
        Carga un nuevo árbol de búsqueda, calcula las coordenadas espaciales
        de cada nodo y ajusta automáticamente la vista para centrarlo.
        """
        self.root_node = root_node
        self.selected_node = None
        self.node_positions.clear()
        self.subtree_bboxes.clear()
        self.node_map.clear()
        self.node_boxes.clear()

        if self.root_node is None:
            self.canvas.delete("all")
            self._draw_empty_message()
            return

        self._collect_and_layout_tree()
        self.fit_to_view()

    def _draw_empty_message(self):
        """Muestra un mensaje informativo cuando no hay un árbol generado."""
        w = self.canvas.winfo_width() or 500
        h = self.canvas.winfo_height() or 400
        self.canvas.create_text(
            w / 2, h / 2 - 10,
            text="🌿 Árbol de Búsqueda",
            font=("Segoe UI", 16, "bold"),
            fill="#cbd5e1"
        )
        self.canvas.create_text(
            w / 2, h / 2 + 18,
            text="Selecciona el algoritmo y presiona Resolver para visualizar la exploración en tiempo real.",
            font=("Segoe UI", 10),
            fill="#94a3b8"
        )

    def _collect_and_layout_tree(self):
        """
        Calcula las posiciones (X, Y) de cada nodo en el plano 2D usando un algoritmo
        de distribución jerárquica por ancho de subárbol para evitar solapamientos.
        """
        if not self.root_node:
            return

        # 1. Recolectar todos los nodos en un diccionario indexado por id
        def collect_nodes(n: Node):
            self.node_map[n.id] = n
            for c in n.children:
                collect_nodes(c)

        collect_nodes(self.root_node)

        # 2. Calcular recursivamente el ancho espacial requerido por cada subárbol
        subtree_widths: Dict[int, float] = {}

        def compute_subtree_width(n: Node) -> float:
            if not n.children:
                w = self.node_width + self.node_gap_x
                subtree_widths[n.id] = w
                return w
            w = sum(compute_subtree_width(c) for c in n.children)
            subtree_widths[n.id] = max(w, self.node_width + self.node_gap_x)
            return subtree_widths[n.id]

        compute_subtree_width(self.root_node)

        # 3. Asignar coordenadas X centradas y coordenadas Y por nivel de profundidad
        def assign_positions(n: Node, left_x: float, depth: int):
            w = subtree_widths[n.id]
            center_x = left_x + w / 2.0
            center_y = depth * self.level_gap_y + 50.0
            self.node_positions[n.id] = (center_x, center_y)

            curr_x = left_x
            for c in n.children:
                child_w = subtree_widths[c.id]
                assign_positions(c, curr_x, depth + 1)
                curr_x += child_w

        assign_positions(self.root_node, 0.0, 0)

        # 4. Calcular Bounding Boxes de subárboles para Frustum Culling jerárquico en O(1)
        def compute_bboxes(n: Node) -> Tuple[float, float, float, float]:
            cx, cy = self.node_positions[n.id]
            w_half = self.node_width / 2.0
            h_half = self.node_height / 2.0
            min_x, max_x = cx - w_half, cx + w_half
            min_y, max_y = cy - h_half, cy + h_half

            for c in n.children:
                c_min_x, c_min_y, c_max_x, c_max_y = compute_bboxes(c)
                min_x = min(min_x, c_min_x)
                max_x = max(max_x, c_max_x)
                min_y = min(min_y, c_min_y)
                max_y = max(max_y, c_max_y)

            self.subtree_bboxes[n.id] = (min_x, min_y, max_x, max_y)
            return (min_x, min_y, max_x, max_y)

        compute_bboxes(self.root_node)

    def fit_to_view(self):
        """
        Calcula la escala de zoom y desplazamiento pan exactos para que todo
        el árbol encaje perfectamente centrado en el área visible del canvas.
        """
        if not self.node_positions:
            return

        self.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw <= 20 or ch <= 20:
            return

        xs = [pos[0] for pos in self.node_positions.values()]
        ys = [pos[1] for pos in self.node_positions.values()]

        min_x, max_x = min(xs) - self.node_width / 2.0, max(xs) + self.node_width / 2.0
        min_y, max_y = min(ys) - self.node_height / 2.0, max(ys) + self.node_height / 2.0

        tree_w = max(max_x - min_x, 10.0)
        tree_h = max(max_y - min_y, 10.0)

        padding = 50.0
        scale_x = (cw - padding * 2) / tree_w
        scale_y = (ch - padding * 2) / tree_h

        # Limitar la escala máxima para que árboles pequeños no se vean desproporcionados
        self.zoom_scale = max(0.06, min(1.15, min(scale_x, scale_y)))

        center_tree_x = (min_x + max_x) / 2.0
        self.pan_x = (cw / 2.0) - (center_tree_x * self.zoom_scale)
        self.pan_y = 40.0 - (min_y * self.zoom_scale)

        self.redraw()

    def _on_resize(self):
        """Maneja el redimensionamiento de la ventana para autoajustar si es necesario."""
        if self.root_node and not self.node_positions:
            self.fit_to_view()

    def _on_mouse_down(self, event):
        """Registra el punto inicial del clic para iniciar el arrastre (Pan)."""
        self.start_drag_x = event.x
        self.start_drag_y = event.y
        self._has_dragged = False

    def _on_mouse_drag(self, event):
        """Actualiza las coordenadas pan_x y pan_y al arrastrar el ratón."""
        dx = event.x - self.start_drag_x
        dy = event.y - self.start_drag_y
        if abs(dx) > 3 or abs(dy) > 3:
            self._has_dragged = True
        self.pan_x += dx
        self.pan_y += dy
        self.start_drag_x = event.x
        self.start_drag_y = event.y
        self.redraw()

    def _on_mouse_up(self, event):
        """
        Si fue un clic simple (sin arrastre prolongado), detecta si se seleccionó un nodo.
        """
        if not self._has_dragged:
            # Transformar coordenadas de pantalla a coordenadas del mundo 2D
            world_x = (event.x - self.pan_x) / self.zoom_scale
            world_y = (event.y - self.pan_y) / self.zoom_scale

            clicked_node_id = None
            for nid, (x1, y1, x2, y2) in self.node_boxes.items():
                if x1 <= world_x <= x2 and y1 <= world_y <= y2:
                    clicked_node_id = nid
                    break

            # Si se hizo clic sobre un nodo, seleccionarlo y notificar a la aplicación
            if clicked_node_id is not None:
                self.selected_node = self.node_map.get(clicked_node_id)
                self.redraw()
                if self.on_node_click and self.selected_node:
                    self.on_node_click(self.selected_node)

    def _on_mouse_wheel(self, event):
        """Maneja el zoom con la rueda del ratón hacia el cursor en Windows."""
        factor = 1.15 if event.delta > 0 else 0.85
        self._zoom(factor, event.x, event.y)

    def _zoom(self, factor: float, center_x: Optional[float] = None, center_y: Optional[float] = None):
        """
        Aplica una escala de zoom centrada sobre un punto pivote (por defecto el centro del canvas).
        """
        cw = self.canvas.winfo_width() or 400
        ch = self.canvas.winfo_height() or 400

        if center_x is None:
            center_x = cw / 2.0
        if center_y is None:
            center_y = ch / 2.0

        new_scale = max(0.04, min(3.0, self.zoom_scale * factor))
        ratio = new_scale / self.zoom_scale

        # Ajustar el pan para que el punto bajo el cursor se mantenga estacionario durante el zoom
        self.pan_x = center_x - (center_x - self.pan_x) * ratio
        self.pan_y = center_y - (center_y - self.pan_y) * ratio
        self.zoom_scale = new_scale

        self.redraw()

    def redraw(self):
        """
        Redibuja el árbol completo utilizando Viewport Frustum Culling.
        Solo los nodos y aristas visibles en pantalla se procesan y renderizan.
        """
        self.canvas.delete("all")
        self.node_boxes.clear()

        if not self.root_node or not self.node_positions:
            self._draw_empty_message()
            return

        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600

        # Rango visible del viewport en coordenadas del mundo (con margen de 80px para suavidad)
        margin_world = 80.0 / self.zoom_scale
        v_min_x = -self.pan_x / self.zoom_scale - margin_world
        v_max_x = (cw - self.pan_x) / self.zoom_scale + margin_world
        v_min_y = -self.pan_y / self.zoom_scale - margin_world
        v_max_y = (ch - self.pan_y) / self.zoom_scale + margin_world

        # =====================================================================
        # 1. DIBUJAR ARISTAS Y CONECTORES (Curvas Bézier con Culling de Subárbol)
        # =====================================================================
        def draw_edges(n: Node):
            # Si el subárbol completo está fuera del viewport visible, descartar rama en O(1)
            sb = self.subtree_bboxes.get(n.id)
            if sb:
                sb_min_x, sb_min_y, sb_max_x, sb_max_y = sb
                if sb_max_x < v_min_x or sb_min_x > v_max_x or sb_max_y < v_min_y or sb_min_y > v_max_y:
                    return

            px, py = self.node_positions[n.id]
            screen_px = px * self.zoom_scale + self.pan_x
            screen_py = (py + self.node_height / 2.0) * self.zoom_scale + self.pan_y

            for c in n.children:
                cx, cy = self.node_positions[c.id]
                screen_cx = cx * self.zoom_scale + self.pan_x
                screen_cy = (cy - self.node_height / 2.0) * self.zoom_scale + self.pan_y

                # Colorear en verde esmeralda brillante si ambos nodos pertenecen a la solución óptima
                is_sol_edge = (n.is_solution and c.is_solution)
                line_color = "#10b981" if is_sol_edge else "#cbd5e1"
                line_width = max(2.5, 3.8 * self.zoom_scale) if is_sol_edge else max(1.2, 1.8 * self.zoom_scale)

                mid_y = (screen_py + screen_cy) / 2.0

                # Resplandor suave para el camino solución
                if is_sol_edge and self.zoom_scale > 0.3:
                    self.canvas.create_line(
                        screen_px, screen_py,
                        screen_px, mid_y,
                        screen_cx, mid_y,
                        screen_cx, screen_cy,
                        fill="#d1fae5",
                        width=line_width + 4 * self.zoom_scale,
                        smooth=True
                    )

                # Línea conector suave
                self.canvas.create_line(
                    screen_px, screen_py,
                    screen_px, mid_y,
                    screen_cx, mid_y,
                    screen_cx, screen_cy,
                    fill=line_color,
                    width=line_width,
                    smooth=True
                )

                # Badge flotante con la acción realizada
                if self.zoom_scale > 0.45 and c.action:
                    badge_x = (screen_px + screen_cx) / 2.0
                    badge_y = mid_y

                    action_icons = {
                        "Arriba": "▲ Arr",
                        "Abajo": "▼ Abj",
                        "Izquierda": "◀ Izq",
                        "Derecha": "▶ Der"
                    }
                    act_label = action_icons.get(c.action, c.action)

                    bw = max(26, int(38 * self.zoom_scale))
                    bh = max(12, int(15 * self.zoom_scale))

                    self.canvas.create_rectangle(
                        badge_x - bw / 2, badge_y - bh / 2,
                        badge_x + bw / 2, badge_y + bh / 2,
                        fill="#ffffff", outline=line_color, width=1
                    )
                    self.canvas.create_text(
                        badge_x, badge_y,
                        text=act_label,
                        font=("Segoe UI", max(6, int(7.5 * self.zoom_scale)), "bold"),
                        fill="#334155"
                    )

                draw_edges(c)

        draw_edges(self.root_node)

        # =====================================================================
        # 2. DIBUJAR TARJETAS DE NODOS (Con Viewport Frustum Culling)
        # =====================================================================
        w_half = self.node_width / 2.0
        h_half = self.node_height / 2.0

        for nid, (wx, wy) in self.node_positions.items():
            box_x1, box_y1 = wx - w_half, wy - h_half
            box_x2, box_y2 = wx + w_half, wy + h_half
            self.node_boxes[nid] = (box_x1, box_y1, box_x2, box_y2)

            # CULLING: Si el nodo está fuera del área visible de la ventana, OMITIR renderizado
            if box_x2 < v_min_x or box_x1 > v_max_x or box_y2 < v_min_y or box_y1 > v_max_y:
                continue

            node = self.node_map[nid]

            # Coordenadas transformadas a espacio de pantalla (píxeles)
            sx1 = box_x1 * self.zoom_scale + self.pan_x
            sy1 = box_y1 * self.zoom_scale + self.pan_y
            sx2 = box_x2 * self.zoom_scale + self.pan_x
            sy2 = box_y2 * self.zoom_scale + self.pan_y

            # Determinar estilo visual según el rol del nodo
            is_selected = (node == self.selected_node)
            is_root = (node == self.root_node)
            is_solution = node.is_solution
            is_expanded = node.is_expanded

            if is_selected:
                card_bg = "#fefce8"
                header_bg = "#facc15"
                border_color = "#eab308"
                border_width = max(2, int(3 * self.zoom_scale))
            elif is_root:
                card_bg = "#faf5ff"
                header_bg = "#c084fc"
                border_color = "#9333ea"
                border_width = max(2, int(2.5 * self.zoom_scale))
            elif is_solution:
                card_bg = "#f0fdf4"
                header_bg = "#4ade80"
                border_color = "#16a34a"
                border_width = max(2, int(2.5 * self.zoom_scale))
            elif is_expanded:
                card_bg = "#f0f9ff"
                header_bg = "#7dd3fc"
                border_color = "#0284c7"
                border_width = max(1, int(1.8 * self.zoom_scale))
            else:
                card_bg = "#ffffff"
                header_bg = "#e2e8f0"
                border_color = "#94a3b8"
                border_width = 1

            # Sombra suave de la tarjeta
            if self.zoom_scale > 0.25:
                shadow_offset = max(2, int(3 * self.zoom_scale))
                self.canvas.create_rectangle(
                    sx1 + shadow_offset, sy1 + shadow_offset,
                    sx2 + shadow_offset, sy2 + shadow_offset,
                    fill="#e2e8f0", outline=""
                )

            # Fondo de la tarjeta
            self.canvas.create_rectangle(
                sx1, sy1, sx2, sy2,
                fill=card_bg,
                outline=border_color,
                width=border_width
            )

            # Barra superior de la tarjeta (Header)
            header_h = (sy2 - sy1) * 0.24
            self.canvas.create_rectangle(
                sx1, sy1, sx2, sy1 + header_h,
                fill=header_bg,
                outline=border_color,
                width=1
            )

            # Texto del Header (ID del Nodo y Acción)
            if self.zoom_scale > 0.35:
                status_text = "Inicio" if is_root else (node.action or "")
                header_title = f"#{node.id} • {status_text}" if status_text else f"Nodo #{node.id}"
                font_header_size = max(6, min(9, int(7.0 * self.zoom_scale)))
                self.canvas.create_text(
                    (sx1 + sx2) / 2.0, sy1 + header_h / 2.0,
                    text=header_title,
                    font=("Segoe UI", font_header_size, "bold"),
                    fill="#0f172a"
                )

            # Cuerpo interno de la tarjeta: Mini Tablero 3x3 a la izquierda + Métricas a la derecha
            if self.zoom_scale > 0.38:
                body_y1 = sy1 + header_h + 3 * self.zoom_scale
                body_y2 = sy2 - 3 * self.zoom_scale

                # Mini tablero 3x3 gráfico
                mini_size = (body_y2 - body_y1) * 0.88
                mini_x1 = sx1 + 8 * self.zoom_scale
                mini_y1 = body_y1 + (body_y2 - body_y1 - mini_size) / 2.0
                tile_dim = mini_size / 3.0

                for tidx, val in enumerate(node.state.tiles):
                    tr, tc = tidx // 3, tidx % 3
                    tx1 = mini_x1 + tc * tile_dim
                    ty1 = mini_y1 + tr * tile_dim
                    tx2 = tx1 + tile_dim - 0.5
                    ty2 = ty1 + tile_dim - 0.5

                    if val == 0:
                        tfill = "#f8fafc"
                        tborder = "#cbd5e1"
                    else:
                        is_goal_pos = (DEFAULT_GOAL[tidx] == val)
                        tfill = "#10b981" if is_goal_pos else "#3b82f6"
                        tborder = "#ffffff"

                    self.canvas.create_rectangle(
                        tx1, ty1, tx2, ty2,
                        fill=tfill, outline=tborder, width=0.5
                    )

                    # Mostrar número de ficha en el mini tablero con zoom suficiente
                    if self.zoom_scale > 0.65 and val != 0:
                        self.canvas.create_text(
                            (tx1 + tx2) / 2.0, (ty1 + ty2) / 2.0,
                            text=str(val),
                            font=("Segoe UI", max(5, int(6.0 * self.zoom_scale)), "bold"),
                            fill="#ffffff"
                        )

                # Bloque de Métricas (f, g, h) a la derecha
                metrics_x = mini_x1 + mini_size + 10 * self.zoom_scale
                metrics_mid_y = (body_y1 + body_y2) / 2.0

                font_f_size = max(7, min(11, int(9.5 * self.zoom_scale)))
                font_gh_size = max(6, min(9, int(7.5 * self.zoom_scale)))

                # Valor principal de evaluación f(n)
                self.canvas.create_text(
                    metrics_x, metrics_mid_y - 9 * self.zoom_scale,
                    text=f"f = {node.f}",
                    font=("Segoe UI", font_f_size, "bold"),
                    fill="#0f172a",
                    anchor=tk.W
                )

                # Costo real acumulado g(n) y heurística h(n)
                self.canvas.create_text(
                    metrics_x, metrics_mid_y + 8 * self.zoom_scale,
                    text=f"g:{node.g}   h:{node.h}",
                    font=("Segoe UI", font_gh_size),
                    fill="#475569",
                    anchor=tk.W
                )
            elif self.zoom_scale > 0.18:
                # Nivel de zoom intermedio: resumen textual
                self.canvas.create_text(
                    (sx1 + sx2) / 2.0, (sy1 + sy2) / 2.0 + 3 * self.zoom_scale,
                    text=f"f = {node.f}\ng:{node.g} h:{node.h}",
                    font=("Segoe UI", max(6, int(8.0 * self.zoom_scale)), "bold"),
                    fill="#0f172a",
                    justify=tk.CENTER
                )
