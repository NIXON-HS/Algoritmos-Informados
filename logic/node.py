"""
==============================================================================
MÓDULO: node.py
PROPÓSITO: Representación de un nodo en el árbol de búsqueda para el 8-Puzzle.
           Almacena costos de ruta g(n), heurística h(n), función f(n),
           punteros al padre/hijos y utilidades de reconstrucción de soluciones.
==============================================================================
"""

from typing import Optional, List, Tuple
from .puzzle_state import PuzzleState


class Node:
    """
    Representa un nodo individual dentro del árbol de búsqueda.
    
    Atributos principales:
    - id: Identificador único autoincremental para diferenciar nodos y visualizarlos en el árbol.
    - state: Configuración del 8-Puzzle representada por este nodo.
    - parent: Referencia al nodo padre desde el cual se generó este estado (None si es la raíz).
    - action: Nombre del movimiento que llevó a este estado ('Arriba', 'Abajo', 'Izquierda', 'Derecha').
    - g: Costo real acumulado desde el nodo raíz hasta este nodo (profundidad / número de pasos).
    - h: Estimación heurística de la distancia de Manhattan restante hasta el objetivo.
    - f: Función de evaluación:
         * En Búsqueda Voraz: f(n) = h(n)
         * En Búsqueda A*:     f(n) = g(n) + h(n)
    - children: Lista de nodos hijos generados a partir de este nodo al expandirlo.
    - is_expanded: Booleano que indica si el nodo ya fue extraído de la frontera y expandido.
    - is_solution: Booleano que indica si el nodo forma parte del camino solución óptimo encontrado.
    """

    _id_counter: int = 0  # Contador de clase estático para asignar IDs únicos

    def __init__(
        self,
        state: PuzzleState,
        parent: Optional["Node"] = None,
        action: Optional[str] = None,
        g: int = 0,
        h: int = 0,
        f: int = 0
    ):
        """
        Inicializa un nuevo nodo del árbol de búsqueda.
        """
        Node._id_counter += 1
        self.id: int = Node._id_counter
        self.state: PuzzleState = state
        self.parent: Optional["Node"] = parent
        self.action: Optional[str] = action
        self.g: int = g
        self.h: int = h
        self.f: int = f
        self.children: List["Node"] = []
        self.is_expanded: bool = False
        self.is_solution: bool = False

    @classmethod
    def reset_counter(cls):
        """
        Reinicia el contador de identificadores de nodos.
        Debe llamarse al inicio de cada nueva búsqueda para que la raíz siempre empiece con ID #1.
        """
        cls._id_counter = 0

    def add_child(self, child: "Node"):
        """
        Registra un nuevo nodo hijo en la estructura jerárquica del árbol.
        """
        self.children.append(child)

    def get_path(self) -> List["Node"]:
        """
        Reconstruye y retorna la secuencia ordenada de nodos desde la raíz hasta este nodo.
        
        :return: Lista de instancias de Node [Raíz, Paso1, Paso2, ..., EsteNodo].
        """
        path = []
        curr: Optional["Node"] = self
        while curr is not None:
            path.append(curr)
            curr = curr.parent
        path.reverse()  # Invertir para que vaya desde la raíz hacia el objetivo
        return path

    def get_solution_actions(self) -> List[str]:
        """
        Retorna la lista ordenada de acciones realizadas para alcanzar este estado.
        
        :return: Lista de strings con los nombres de movimientos ['Arriba', 'Derecha', ...].
        """
        path = self.get_path()
        return [node.action for node in path[1:] if node.action is not None]

    def mark_solution_path(self):
        """
        Recorre hacia atrás desde este nodo hasta la raíz marcando cada nodo
        con is_solution = True para resaltarlo visualmente en el árbol gráfico.
        """
        curr: Optional["Node"] = self
        while curr is not None:
            curr.is_solution = True
            curr = curr.parent

    def __lt__(self, other: "Node") -> bool:
        """
        Criterio de ordenamiento para la Cola de Prioridad (heapq):
        1. Menor valor de evaluación f(n).
        2. En caso de empate en f, desempata por menor heurística h(n) (más cercano a la meta).
        3. En caso de empate en h, desempata por orden de creación (id).
        """
        if self.f != other.f:
            return self.f < other.f
        if self.h != other.h:
            return self.h < other.h
        return self.id < other.id

    def __repr__(self) -> str:
        return f"Node(id={self.id}, g={self.g}, h={self.h}, f={self.f}, act={self.action})"
