"""
==============================================================================
MÓDULO: custom_state_dialog.py
PROPÓSITO: Diálogo modal interactivo con cuadrícula 3x3 de casillas editables
           directas. Permite escribir el número (0 al 8) dentro de cada cuadro
           con auto-avance, navegación por flechas, presets y validación en vivo.
==============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict
from logic.puzzle_state import PuzzleState, DEFAULT_GOAL, PRESET_STATES


class CustomStateDialog(tk.Toplevel):
    """
    Ventana modal interactiva con cuadrícula 3x3 editable directa para configurar el 8-Puzzle.
    """

    def __init__(self, parent, current_state: PuzzleState, goal_state: PuzzleState):
        super().__init__(parent)
        self.title("Configurar Estado Inicial - 8-Puzzle")
        self.geometry("460x580")
        self.minsize(420, 540)
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # Comportamiento modal
        self.transient(parent)
        self.grab_set()

        self.current_state = current_state
        self.goal_state = goal_state
        self.result_state: Optional[PuzzleState] = None

        # Variables de las 9 casillas editables
        self.tile_vars: List[tk.StringVar] = [tk.StringVar() for _ in range(9)]
        self.tile_entries: List[tk.Entry] = []
        self.tile_frames: List[tk.Frame] = []

        self._build_ui()
        self._center_window(parent)

        # Cargar valores actuales en la cuadrícula 3x3
        for idx, val in enumerate(current_state.tiles):
            self.tile_vars[idx].set(str(val))

        self._validate_grid()

        # Enfocar la primera casilla
        if self.tile_entries:
            self.tile_entries[0].focus_set()
            self.tile_entries[0].select_range(0, tk.END)

        # Esperar hasta que se cierre la ventana
        self.wait_window(self)

    def _center_window(self, parent):
        """Centra la ventana modal sobre la ventana principal."""
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        w = self.winfo_width()
        h = self.winfo_height()

        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # 1. ENCABEZADO
        header_frame = tk.Frame(self, bg="#2563eb", padx=20, pady=12)
        header_frame.pack(fill=tk.X)

        lbl_header_title = tk.Label(
            header_frame,
            text="✏️ Configurar Tablero 3x3",
            font=("Segoe UI", 13, "bold"),
            bg="#2563eb",
            fg="#ffffff"
        )
        lbl_header_title.pack(anchor=tk.W)

        lbl_header_sub = tk.Label(
            header_frame,
            text="Escribe directamente en cada casilla los números del 0 al 8 (0 = espacio vacío).",
            font=("Segoe UI", 8),
            bg="#2563eb",
            fg="#bfdbfe"
        )
        lbl_header_sub.pack(anchor=tk.W, pady=(2, 0))

        # CUERPO PRINCIPAL
        body_frame = tk.Frame(self, bg="#f8fafc", padx=20, pady=12)
        body_frame.pack(fill=tk.BOTH, expand=True)

        # 2. BARRA DE ACCIONES RÁPIDAS
        quick_frame = tk.Frame(body_frame, bg="#f8fafc")
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        btn_rnd = tk.Button(
            quick_frame, text="🎲 Aleatorio", font=("Segoe UI", 8, "bold"),
            bg="#ffffff", fg="#334155", activebackground="#f1f5f9",
            relief=tk.SOLID, bd=1, padx=6, pady=3, cursor="hand2",
            command=self._set_random
        )
        btn_rnd.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        btn_goal = tk.Button(
            quick_frame, text="🎯 Meta", font=("Segoe UI", 8, "bold"),
            bg="#ffffff", fg="#334155", activebackground="#f1f5f9",
            relief=tk.SOLID, bd=1, padx=6, pady=3, cursor="hand2",
            command=self._set_goal
        )
        btn_goal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.preset_var = tk.StringVar(value="Cargar Ejemplo...")
        preset_names = ["Cargar Ejemplo..."] + list(PRESET_STATES.keys())
        self.cb_presets = ttk.Combobox(
            quick_frame,
            textvariable=self.preset_var,
            values=preset_names,
            state="readonly",
            font=("Segoe UI", 8),
            width=16
        )
        self.cb_presets.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))
        self.cb_presets.bind("<<ComboboxSelected>>", self._on_preset_selected)

        # 3. CUADRÍCULA 3x3 DE ENTRADAS EDITABLES DIRECTAS
        grid_container = tk.Frame(body_frame, bg="#e2e8f0", bd=2, relief=tk.SOLID, padx=8, pady=8, highlightbackground="#94a3b8")
        grid_container.pack(pady=(2, 10))

        for idx in range(9):
            row, col = idx // 3, idx % 3

            cell_frame = tk.Frame(
                grid_container,
                bg="#ffffff",
                bd=2,
                relief=tk.SOLID,
                highlightthickness=1,
                highlightbackground="#cbd5e1",
                width=72,
                height=72
            )
            cell_frame.grid(row=row, column=col, padx=4, pady=4)
            cell_frame.pack_propagate(False)

            entry = tk.Entry(
                cell_frame,
                textvariable=self.tile_vars[idx],
                font=("Segoe UI", 22, "bold"),
                bg="#ffffff",
                fg="#0f172a",
                justify=tk.CENTER,
                relief=tk.FLAT,
                bd=0
            )
            entry.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)

            # Eventos para navegación ágil y auto-avance
            entry.bind("<KeyRelease>", lambda e, i=idx: self._on_key_release(e, i))
            entry.bind("<FocusIn>", lambda e, i=idx: self._on_focus_in(i))
            entry.bind("<FocusOut>", lambda e, i=idx: self._on_focus_out(i))
            entry.bind("<Up>", lambda e, i=idx: self._navigate(i, -3))
            entry.bind("<Down>", lambda e, i=idx: self._navigate(i, 3))
            entry.bind("<Left>", lambda e, i=idx: self._navigate(i, -1))
            entry.bind("<Right>", lambda e, i=idx: self._navigate(i, 1))

            self.tile_entries.append(entry)
            self.tile_frames.append(cell_frame)

        # 4. BADGE DE VALIDACIÓN Y SOLUBILIDAD EN VIVO
        self.status_frame = tk.Frame(body_frame, bg="#f1f5f9", padx=8, pady=6, bd=1, relief=tk.SOLID)
        self.status_frame.pack(fill=tk.X, pady=(0, 8))

        self.lbl_status_icon = tk.Label(self.status_frame, text="ℹ️", font=("Segoe UI", 10), bg="#f1f5f9")
        self.lbl_status_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_status_text = tk.Label(
            self.status_frame,
            text="Escribe los números del 0 al 8 en las casillas.",
            font=("Segoe UI", 8),
            bg="#f1f5f9",
            fg="#475569",
            wraplength=360,
            justify=tk.LEFT
        )
        self.lbl_status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 5. BOTONES DE PIE (Aplicar / Cancelar)
        footer_frame = tk.Frame(self, bg="#f1f5f9", padx=20, pady=12, bd=1, relief=tk.SOLID)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_cancel = tk.Button(
            footer_frame, text="Cancelar", font=("Segoe UI", 9, "bold"),
            bg="#ffffff", fg="#475569", activebackground="#f1f5f9",
            relief=tk.SOLID, bd=1, padx=14, pady=5, cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_apply = tk.Button(
            footer_frame, text="💾 Aplicar Estado", font=("Segoe UI", 9, "bold"),
            bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff",
            relief=tk.FLAT, padx=16, pady=5, cursor="hand2",
            command=self._apply_state
        )
        self.btn_apply.pack(side=tk.RIGHT)

    def _on_focus_in(self, idx: int):
        """Resalta la casilla activa y selecciona todo su texto."""
        self.tile_frames[idx].configure(highlightbackground="#2563eb", bd=2)
        self.tile_entries[idx].select_range(0, tk.END)

    def _on_focus_out(self, idx: int):
        """Restaura el borde al perder el foco."""
        self._update_cell_appearance(idx)

    def _navigate(self, curr_idx: int, delta: int):
        """Mueve el foco entre casillas con las teclas de flechas."""
        target = curr_idx + delta
        if 0 <= target < 9:
            self.tile_entries[target].focus_set()
            self.tile_entries[target].select_range(0, tk.END)

    def _on_key_release(self, event, idx: int):
        """Maneja la entrada del usuario con auto-avance inteligente a la siguiente casilla."""
        val = self.tile_vars[idx].get().strip()

        # Si el usuario presionó teclas especiales, no avanzar
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Up", "Down", "Tab"):
            self._validate_grid()
            return

        # Si escribió más de 1 caracter, conservar el último
        if len(val) > 1:
            val = val[-1]
            self.tile_vars[idx].set(val)

        # Si escribió un dígito válido del 0 al 8, pasar automáticamente a la siguiente casilla
        if val in "012345678":
            if idx < 8:
                self.tile_entries[idx + 1].focus_set()
                self.tile_entries[idx + 1].select_range(0, tk.END)

        self._validate_grid()

    def _update_cell_appearance(self, idx: int):
        """Aplica colores estilizados a cada casilla según su valor."""
        raw = self.tile_vars[idx].get().strip()
        frame = self.tile_frames[idx]
        entry = self.tile_entries[idx]

        if not raw or not raw.isdigit():
            frame.configure(bg="#ffffff", highlightbackground="#cbd5e1")
            entry.configure(bg="#ffffff", fg="#0f172a")
            return

        val = int(raw)
        if val == 0:
            frame.configure(bg="#f1f5f9", highlightbackground="#94a3b8")
            entry.configure(bg="#f1f5f9", fg="#64748b")
        else:
            is_goal = (DEFAULT_GOAL[idx] == val)
            bg_color = "#f0fdf4" if is_goal else "#eff6ff"
            border_color = "#16a34a" if is_goal else "#3b82f6"
            text_color = "#15803d" if is_goal else "#1d4ed8"

            frame.configure(bg=bg_color, highlightbackground=border_color)
            entry.configure(bg=bg_color, fg=text_color)

    def _validate_grid(self):
        """Valida los 9 números de la cuadrícula, actualiza estilos y el badge de solubilidad."""
        vals = []
        is_complete = True

        for idx in range(9):
            self._update_cell_appearance(idx)
            raw = self.tile_vars[idx].get().strip()
            if not raw or not raw.isdigit():
                is_complete = False
            else:
                v = int(raw)
                if not (0 <= v <= 8):
                    is_complete = False
                vals.append(v)

        if not is_complete or len(vals) != 9:
            self._set_status(
                icon="⏳",
                text="Completa las 9 casillas con los números del 0 al 8.",
                bg="#fffbeb",
                border="#fde68a",
                fg="#b45309",
                valid=False
            )
            return

        # Validar dígitos únicos sin duplicados
        if sorted(vals) != list(range(9)):
            dup = [x for x in set(vals) if vals.count(x) > 1]
            self._set_status(
                icon="⚠️",
                text=f"Números repetidos: {dup}. Cada número del 0 al 8 debe aparecer una sola vez.",
                bg="#fffbeb",
                border="#fde68a",
                fg="#b45309",
                valid=False
            )
            return

        # Validar Solubilidad
        state = PuzzleState(tuple(vals))
        is_solv = state.is_solvable(self.goal_state)
        manhattan = state.manhattan_distance(self.goal_state)

        if is_solv:
            self._set_status(
                icon="✅",
                text=f"Estado Válido y Resoluble • Heurística Manhattan h(n) = {manhattan}",
                bg="#f0fdf4",
                border="#86efac",
                fg="#15803d",
                valid=True
            )
        else:
            self._set_status(
                icon="🚫",
                text="Estado Insoluble (Paridad de inversiones impar no alcanza la meta).",
                bg="#fef2f2",
                border="#fca5a5",
                fg="#b91c1c",
                valid=False,
                allow_anyway=True
            )

    def _set_status(self, icon: str, text: str, bg: str, border: str, fg: str, valid: bool, allow_anyway: bool = False):
        """Actualiza el badge de estado y habilita/deshabilita el botón de aplicar."""
        self.status_frame.configure(bg=bg, highlightbackground=border)
        self.lbl_status_icon.configure(text=icon, bg=bg)
        self.lbl_status_text.configure(text=text, bg=bg, fg=fg)

        if valid or allow_anyway:
            self.btn_apply.configure(state=tk.NORMAL)
        else:
            self.btn_apply.configure(state=tk.DISABLED)

    def _set_random(self):
        """Genera un estado aleatorio resoluble y lo coloca en las 9 casillas."""
        st = PuzzleState.create_random_solvable(self.goal_state)
        for idx, val in enumerate(st.tiles):
            self.tile_vars[idx].set(str(val))
        self._validate_grid()

    def _set_goal(self):
        """Carga el estado meta en la cuadrícula."""
        for idx, val in enumerate(DEFAULT_GOAL):
            self.tile_vars[idx].set(str(val))
        self._validate_grid()

    def _on_preset_selected(self, event=None):
        """Carga un ejemplo predefinido en la cuadrícula."""
        key = self.preset_var.get()
        if key in PRESET_STATES:
            for idx, val in enumerate(PRESET_STATES[key]):
                self.tile_vars[idx].set(str(val))
            self._validate_grid()

    def _apply_state(self):
        """Aplica la configuración del tablero y cierra el diálogo modal."""
        vals = []
        for idx in range(9):
            raw = self.tile_vars[idx].get().strip()
            if not raw or not raw.isdigit():
                messagebox.showerror("Incompleto", "Por favor completa todas las casillas.", parent=self)
                return
            vals.append(int(raw))

        try:
            new_state = PuzzleState(tuple(vals))
            if not new_state.is_solvable(self.goal_state):
                resp = messagebox.askyesno(
                    "Estado No Resoluble",
                    "La configuración ingresada tiene distinta paridad de inversiones y NO es resoluble hacia el objetivo.\n\n¿Desea mantenerla de todos modos?",
                    parent=self
                )
                if not resp:
                    return

            self.result_state = new_state
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error en el estado: {e}", parent=self)
