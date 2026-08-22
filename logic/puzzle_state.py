"""
==============================================================================
MÓDULO: puzzle_state.py
PROPÓSITO: Modelo del estado del 8-Puzzle, cálculo de la Heurística de Manhattan,
           validación de solubilidad mediante inversiones y generación de sucesores.
==============================================================================
"""

import random
from typing import Tuple, List, Optional, Dict

# ==============================================================================
# CONFIGURACIONES Y CONSTANTES DE ESTADOS
# ==============================================================================

# Estado objetivo estándar (Meta clásica del 8-Puzzle):
# 1 2 3
# 4 5 6
# 7 8 0  (donde 0 representa el espacio en blanco)
DEFAULT_GOAL: Tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 0)

# Estado inicial predeterminado determinista para pruebas inmediatas
DEFAULT_INITIAL: Tuple[int, ...] = (1, 2, 3, 4, 0, 6, 7, 5, 8)

# Ejemplos predefinidos deterministas con soluciones a distinta profundidad
PRESET_STATES: Dict[str, Tuple[int, ...]] = {
    "Ejemplo 1 (2 pasos)": (1, 2, 3, 4, 0, 6, 7, 5, 8),
    "Ejemplo 2 (4 pasos)": (1, 2, 3, 0, 4, 6, 7, 5, 8),
    "Ejemplo 3 (6 pasos)": (1, 2, 3, 4, 5, 6, 0, 7, 8),
    "Ejemplo 4 (8 pasos)": (1, 2, 3, 5, 0, 6, 4, 7, 8),
}


class PuzzleState:
    """
    Representa un estado inmutable del 8-Puzzle en una cuadrícula de 3x3.
    
    El estado se almacena internamente como una tupla unidimensional inmutable de 9 enteros (0 al 8).
    El número 0 representa la casilla vacía (espacio en blanco).
    """

    def __init__(self, tiles: Tuple[int, ...]):
        """
        Inicializa un nuevo estado del 8-Puzzle verificando su validez.
        
        :param tiles: Tupla de 9 números del 0 al 8 sin repeticiones.
        :raises ValueError: Si la cantidad de fichas no es 9 o si los números no son del 0 al 8.
        """
        # Validación de longitud exacta de 9 casillas (3x3)
        if len(tiles) != 9:
            raise ValueError(f"El estado debe contener exactamente 9 elementos, recibido: {len(tiles)}")
        
        # Validación de que contenga todos los dígitos del 0 al 8 sin duplicados
        if sorted(tiles) != list(range(9)):
            raise ValueError(f"El estado debe contener los números del 0 al 8 sin repetir, recibido: {tiles}")
        
        self.tiles: Tuple[int, ...] = tuple(tiles)
        self.blank_index: int = self.tiles.index(0)  # Posición lineal (0-8) del espacio en blanco
        self._hash: int = hash(self.tiles)           # Hash precalculado para búsquedas rápidas en sets/dicts

    @property
    def blank_row_col(self) -> Tuple[int, int]:
        """
        Retorna la posición en coordenadas (fila, columna) de base 0 del espacio en blanco (0).
        Fila = índice // 3, Columna = índice % 3.
        """
        return self.blank_index // 3, self.blank_index % 3

    def manhattan_distance(self, goal_state: "PuzzleState" = None) -> int:
        """
        Calcula la función heurística h(n) basada en la Distancia de Manhattan.
        
        Fórmula matemática:
            h(n) = Sumatoria(|x_i - x_meta| + |y_i - y_meta|) para cada ficha i de 1 a 8.
            
        Propiedades teóricas:
        - Es Admisible: Nunca sobreestima el costo real para llegar al objetivo (h(n) <= h*(n)).
        - Es Consistente (Monótona): Cumple la desigualdad triangular h(n) <= c(n, a, n') + h(n').
        
        Nota: La casilla vacía (0) NO se incluye en la sumatoria de distancias.
        
        :param goal_state: Estado objetivo (si es None, usa DEFAULT_GOAL).
        :return: Entero con la distancia de Manhattan total acumulada.
        """
        if goal_state is None:
            goal_state = PuzzleState(DEFAULT_GOAL)

        # Mapear la posición esperada de cada número en la meta: valor -> (fila_meta, col_meta)
        goal_positions = {}
        for idx, val in enumerate(goal_state.tiles):
            if val != 0:
                goal_positions[val] = (idx // 3, idx % 3)

        total_distance = 0
        # Recorrer cada ficha en el estado actual y sumar las distancias horizontales y verticales
        for idx, val in enumerate(self.tiles):
            if val != 0:
                current_r, current_c = idx // 3, idx % 3
                goal_r, goal_c = goal_positions[val]
                total_distance += abs(current_r - goal_r) + abs(current_c - goal_c)

        return total_distance

    def get_successors(self) -> List[Tuple[str, "PuzzleState"]]:
        """
        Genera todos los estados sucesores válidos realizando los movimientos legales
        del espacio en blanco (Arriba, Abajo, Izquierda, Derecha).
        
        :return: Lista de tuplas con el formato (nombre_accion, nuevo_estado_puzzle).
        """
        r, c = self.blank_row_col
        
        # Posibles desplazamientos del espacio en blanco (delta_fila, delta_columna)
        moves = [
            ("Arriba", -1, 0),
            ("Abajo", 1, 0),
            ("Izquierda", 0, -1),
            ("Derecha", 0, 1),
        ]

        successors = []
        tiles_list = list(self.tiles)

        for action, dr, dc in moves:
            nr, nc = r + dr, c + dc
            # Verificar si la nueva posición del blanco cae dentro de los límites de 3x3
            if 0 <= nr < 3 and 0 <= nc < 3:
                new_blank_idx = nr * 3 + nc
                new_tiles = list(tiles_list)
                # Intercambiar el espacio en blanco con la ficha adyacente
                new_tiles[self.blank_index], new_tiles[new_blank_idx] = (
                    new_tiles[new_blank_idx],
                    new_tiles[self.blank_index],
                )
                successors.append((action, PuzzleState(tuple(new_tiles))))

        return successors

    def move_tile_at_index(self, tile_index: int) -> Optional[Tuple[str, "PuzzleState"]]:
        """
        Mueve la ficha ubicada en 'tile_index' hacia el espacio en blanco si es adyacente.
        Utilizado principalmente para la interacción manual por clics del usuario en la GUI.
        
        :param tile_index: Índice lineal (0-8) de la ficha que se desea mover.
        :return: Tupla (acción, nuevo_estado) si el movimiento es legal, o None si no es adyacente.
        """
        if not (0 <= tile_index < 9):
            return None
        
        tr, tc = tile_index // 3, tile_index % 3
        br, bc = self.blank_row_col

        dr, dc = tr - br, tc - bc
        # Debe estar a exactamente 1 paso de distancia Manhattan del espacio en blanco
        if abs(dr) + abs(dc) != 1:
            return None

        # Identificar el nombre de la acción según la dirección del movimiento
        action_map = {
            (-1, 0): "Arriba",
            (1, 0): "Abajo",
            (0, -1): "Izquierda",
            (0, 1): "Derecha"
        }
        action = action_map.get((dr, dc), "Mover")

        # Generar nuevo estado intercambiando fichas
        new_tiles = list(self.tiles)
        new_tiles[self.blank_index], new_tiles[tile_index] = new_tiles[tile_index], new_tiles[self.blank_index]
        return action, PuzzleState(tuple(new_tiles))

    def count_inversions(self) -> int:
        """
        Calcula el número de inversiones de la permutación (omitiendo el 0).
        
        Definición:
            Una inversión ocurre cuando un número mayor aparece antes que un número menor en la lista.
            Ejemplo: En [2, 1, 3] hay 1 inversión porque 2 > 1.
        
        :return: Cantidad total de inversiones.
        """
        tiles_without_zero = [x for x in self.tiles if x != 0]
        inversions = 0
        n = len(tiles_without_zero)
        for i in range(n):
            for j in range(i + 1, n):
                if tiles_without_zero[i] > tiles_without_zero[j]:
                    inversions += 1
        return inversions

    def is_solvable(self, goal_state: "PuzzleState" = None) -> bool:
        """
        Determina matemáticamente si el estado actual es resoluble hacia el estado objetivo.
        
        Teorema de Solubilidad en Cuadrículas Impares (3x3):
            En un tablero 3x3, los movimientos del blanco no alteran la paridad del número de inversiones.
            Por lo tanto, un estado es alcanzable si y solo si la paridad de inversiones
            de dicho estado coincide exactamente con la paridad de inversiones del objetivo.
        
        :param goal_state: Estado objetivo contra el cual se valida.
        :return: True si existe un camino de solución legal, False si es matemáticamente imposible.
        """
        if goal_state is None:
            goal_state = PuzzleState(DEFAULT_GOAL)
        
        return (self.count_inversions() % 2) == (goal_state.count_inversions() % 2)

    @classmethod
    def create_random_solvable(cls, goal_state: "PuzzleState" = None, num_moves: Optional[int] = None) -> "PuzzleState":
        """
        Genera una permutación aleatoria garantizando al 100% que sea resoluble hacia el objetivo.
        
        :param goal_state: Estado meta de referencia.
        :param num_moves: Si se especifica, aplica N pasos aleatorios desde la meta. Si es None, permuta libremente.
        :return: Instancia de PuzzleState matemáticamente resoluble.
        """
        if goal_state is None:
            goal_state = PuzzleState(DEFAULT_GOAL)

        # Generar aplicando movimientos aleatorios válidos desde la meta
        if num_moves is not None:
            curr = goal_state
            for _ in range(num_moves):
                succs = curr.get_successors()
                curr = random.choice(succs)[1]
            return curr

        # Generar barajando aleatoriamente y validando la paridad de inversiones
        while True:
            tiles = list(range(9))
            random.shuffle(tiles)
            state = cls(tuple(tiles))
            if state.is_solvable(goal_state) and state != goal_state:
                return state

    def to_matrix(self) -> List[List[int]]:
        """Retorna una representación en matriz bidimensional de 3x3."""
        return [list(self.tiles[i:i+3]) for i in range(0, 9, 3)]

    def __hash__(self) -> int:
        """Permite usar el estado como clave en tablas hash (sets y diccionarios)."""
        return self._hash

    def __eq__(self, other: object) -> bool:
        """Compara si dos estados tienen exactamente la misma configuración de fichas."""
        if isinstance(other, PuzzleState):
            return self.tiles == other.tiles
        return False

    def __repr__(self) -> str:
        return f"PuzzleState({self.tiles})"

    def __str__(self) -> str:
        """Formato legible en 3 filas para imprimir en consola."""
        res = []
        for i in range(0, 9, 3):
            row = [str(x) if x != 0 else "_" for x in self.tiles[i:i+3]]
            res.append(" ".join(row))
        return "\n".join(res)
