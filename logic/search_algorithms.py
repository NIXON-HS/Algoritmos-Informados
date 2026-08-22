"""
==============================================================================
MÓDULO: search_algorithms.py
PROPÓSITO: Implementación de los algoritmos de Búsqueda Informada para el 8-Puzzle:
           1. Búsqueda Voraz Primero el Mejor (Greedy Best-First Search) [f(n) = h(n)]
           2. Búsqueda A* (A-Star Search) [f(n) = g(n) + h(n)]
           Ambos utilizando la heurística de Distancia de Manhattan.
==============================================================================
"""

import time
import heapq
from typing import Optional, List, Dict, Set, Tuple, Any
from .puzzle_state import PuzzleState, DEFAULT_GOAL
from .node import Node


class SearchResult:
    """
    Estructura de datos que encapsula todos los resultados y métricas
    recolectadas durante la ejecución de un algoritmo de búsqueda.
    """

    def __init__(
        self,
        algorithm_name: str,
        initial_state: PuzzleState,
        goal_state: PuzzleState,
        root_node: Node,
        goal_node: Optional[Node],
        expanded_count: int,
        generated_count: int,
        execution_time_ms: float,
        max_frontier_size: int,
        step_events: List[Dict[str, Any]],
        success: bool = True,
        message: str = "Solución encontrada"
    ):
        """
        :param algorithm_name: Nombre del algoritmo ejecutado ('Búsqueda Voraz' o 'Búsqueda A*').
        :param initial_state: Estado inicial desde el cual partió la búsqueda.
        :param goal_state: Estado objetivo buscado.
        :param root_node: Nodo raíz del árbol de búsqueda generado.
        :param goal_node: Nodo meta alcanzado (None si no se encontró solución).
        :param expanded_count: Cantidad total de nodos extraídos de la frontera y expandidos.
        :param generated_count: Cantidad total de nodos creados e insertados en memoria.
        :param execution_time_ms: Tiempo total de procesamiento en milisegundos.
        :param max_frontier_size: Tamaño máximo alcanzado por la cola de prioridad en memoria.
        :param step_events: Historial de eventos de expansión.
        :param success: Booleano que indica si se alcanzó el objetivo exitosamente.
        :param message: Mensaje informativo del estado de terminación.
        """
        self.algorithm_name = algorithm_name
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.root_node = root_node
        self.goal_node = goal_node
        self.expanded_count = expanded_count
        self.generated_count = generated_count
        self.execution_time_ms = execution_time_ms
        self.max_frontier_size = max_frontier_size
        self.step_events = step_events
        self.success = success
        self.message = message

        # Secuencia ordenada de nodos y acciones de la solución encontrada
        self.solution_path: List[Node] = goal_node.get_path() if goal_node else []
        self.solution_actions: List[str] = goal_node.get_solution_actions() if goal_node else []
        self.solution_cost: int = len(self.solution_actions) if goal_node else 0


def greedy_best_first_search(
    initial_state: PuzzleState,
    goal_state: Optional[PuzzleState] = None,
    max_nodes: int = 40000
) -> SearchResult:
    """
    Ejecuta el algoritmo de Búsqueda Voraz Primero el Mejor (Greedy Best-First Search).
    
    Características:
    - Función de evaluación: f(n) = h(n) (únicamente la heurística de Manhattan).
    - Estrategia: Expande siempre el nodo que parece estar más cerca de la meta.
    - Ventaja: Suele ser muy rápido en encontrar un camino.
    - Desventaja: NO garantiza encontrar la solución óptima (camino con menor número de pasos).
    
    :param initial_state: Configuración inicial del 8-Puzzle.
    :param goal_state: Configuración meta deseada (por defecto DEFAULT_GOAL).
    :param max_nodes: Límite de seguridad de nodos expandidos para evitar consumo excesivo de memoria.
    :return: Instancia de SearchResult con el árbol de búsqueda y métricas completas.
    """
    if goal_state is None:
        goal_state = PuzzleState(DEFAULT_GOAL)

    # Reiniciar contador global de nodos para que la raíz inicie en ID #1
    Node.reset_counter()
    start_time = time.perf_counter()

    # Creación del nodo raíz
    initial_h = initial_state.manhattan_distance(goal_state)
    root_node = Node(
        state=initial_state,
        parent=None,
        action=None,
        g=0,
        h=initial_h,
        f=initial_h  # Voraz: f(n) = h(n)
    )

    # Caso trivial: El estado inicial ya es el objetivo
    if initial_state == goal_state:
        root_node.mark_solution_path()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name="Búsqueda Voraz",
            initial_state=initial_state,
            goal_state=goal_state,
            root_node=root_node,
            goal_node=root_node,
            expanded_count=0,
            generated_count=1,
            execution_time_ms=elapsed_ms,
            max_frontier_size=1,
            step_events=[{"type": "expand", "node": root_node, "frontier": []}]
        )

    # Frontera organizada como min-heap (cola de prioridad ordenada por f = h)
    frontier: List[Node] = []
    heapq.heappush(frontier, root_node)

    # Conjunto de estados visitados para evitar ciclos infinitos y exploraciones redundantes
    visited_states: Set[PuzzleState] = {initial_state}
    
    expanded_count = 0
    generated_count = 1
    max_frontier_size = 1
    step_events = []
    goal_node: Optional[Node] = None

    # Bucle principal de exploración
    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))

        # Extraer el nodo con menor valor heurístico h(n)
        current_node = heapq.heappop(frontier)
        current_node.is_expanded = True
        expanded_count += 1

        step_events.append({
            "type": "expand",
            "node": current_node,
            "frontier_size": len(frontier)
        })

        # Comprobación de meta
        if current_node.state == goal_state:
            goal_node = current_node
            goal_node.mark_solution_path()
            break

        # Control de seguridad de límite de nodos
        if expanded_count >= max_nodes:
            break

        # Expansión de sucesores
        for action, succ_state in current_node.state.get_successors():
            if succ_state not in visited_states:
                visited_states.add(succ_state)
                succ_h = succ_state.manhattan_distance(goal_state)
                child_node = Node(
                    state=succ_state,
                    parent=current_node,
                    action=action,
                    g=current_node.g + 1,
                    h=succ_h,
                    f=succ_h  # Voraz: f = h
                )
                current_node.add_child(child_node)
                generated_count += 1
                heapq.heappush(frontier, child_node)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    success = goal_node is not None
    msg = "Solución encontrada exitosamente" if success else (
        f"Límite de nodos alcanzado ({max_nodes})" if expanded_count >= max_nodes else "No existe solución"
    )

    return SearchResult(
        algorithm_name="Búsqueda Voraz (Greedy)",
        initial_state=initial_state,
        goal_state=goal_state,
        root_node=root_node,
        goal_node=goal_node,
        expanded_count=expanded_count,
        generated_count=generated_count,
        execution_time_ms=elapsed_ms,
        max_frontier_size=max_frontier_size,
        step_events=step_events,
        success=success,
        message=msg
    )


def a_star_search(
    initial_state: PuzzleState,
    goal_state: Optional[PuzzleState] = None,
    max_nodes: int = 50000
) -> SearchResult:
    """
    Ejecuta el algoritmo de Búsqueda A* (A-Star Search).
    
    Características:
    - Función de evaluación: f(n) = g(n) + h(n).
      * g(n): Costo real exacto incurrido desde la raíz hasta el nodo n.
      * h(n): Estimación admisible y consistente de la Distancia de Manhattan restante.
    - Garantía de Optimalidad: Al usar Manhattan (heurística admisible y consistente),
      A* garantiza encontrar el camino con el MÍNIMO número de pasos posible.
    - Completitud: Siempre encuentra la solución si existe.
    
    :param initial_state: Configuración inicial del 8-Puzzle.
    :param goal_state: Configuración meta deseada (por defecto DEFAULT_GOAL).
    :param max_nodes: Límite de seguridad de nodos expandidos.
    :return: Instancia de SearchResult con el árbol óptimo y métricas.
    """
    if goal_state is None:
        goal_state = PuzzleState(DEFAULT_GOAL)

    # Reiniciar contador global de nodos
    Node.reset_counter()
    start_time = time.perf_counter()

    # Creación del nodo raíz
    initial_h = initial_state.manhattan_distance(goal_state)
    root_node = Node(
        state=initial_state,
        parent=None,
        action=None,
        g=0,
        h=initial_h,
        f=initial_h  # En la raíz: f = 0 + h = h
    )

    # Caso trivial: Inicio == Meta
    if initial_state == goal_state:
        root_node.mark_solution_path()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResult(
            algorithm_name="Búsqueda A*",
            initial_state=initial_state,
            goal_state=goal_state,
            root_node=root_node,
            goal_node=root_node,
            expanded_count=0,
            generated_count=1,
            execution_time_ms=elapsed_ms,
            max_frontier_size=1,
            step_events=[{"type": "expand", "node": root_node, "frontier": []}]
        )

    # Cola de prioridad ordenada por f(n) = g(n) + h(n)
    frontier: List[Node] = []
    heapq.heappush(frontier, root_node)

    # Registro del menor costo g conocido para cada estado
    best_g_costs: Dict[PuzzleState, int] = {initial_state: 0}
    # Conjunto cerrado de estados ya expandidos
    closed_set: Set[PuzzleState] = set()

    expanded_count = 0
    generated_count = 1
    max_frontier_size = 1
    step_events = []
    goal_node: Optional[Node] = None

    # Bucle principal de exploración de A*
    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))

        # Extraer el nodo con menor f(n)
        current_node = heapq.heappop(frontier)

        # Si el estado ya fue expandido previamente por un camino de menor o igual costo, ignorar
        if current_node.state in closed_set:
            continue

        closed_set.add(current_node.state)
        current_node.is_expanded = True
        expanded_count += 1

        step_events.append({
            "type": "expand",
            "node": current_node,
            "frontier_size": len(frontier)
        })

        # Comprobación de meta al expandir
        if current_node.state == goal_state:
            goal_node = current_node
            goal_node.mark_solution_path()
            break

        # Control de seguridad de memoria/tiempo
        if expanded_count >= max_nodes:
            break

        # Expansión de sucesores
        for action, succ_state in current_node.state.get_successors():
            tentative_g = current_node.g + 1

            # Si ya fue cerrado con un mejor costo g, no reexaminar
            if succ_state in closed_set and tentative_g >= best_g_costs.get(succ_state, float("inf")):
                continue

            # Si encontramos un camino más corto hacia succ_state
            if tentative_g < best_g_costs.get(succ_state, float("inf")):
                best_g_costs[succ_state] = tentative_g
                succ_h = succ_state.manhattan_distance(goal_state)
                child_node = Node(
                    state=succ_state,
                    parent=current_node,
                    action=action,
                    g=tentative_g,
                    h=succ_h,
                    f=tentative_g + succ_h  # A*: f(n) = g(n) + h(n)
                )
                current_node.add_child(child_node)
                generated_count += 1
                heapq.heappush(frontier, child_node)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    success = goal_node is not None
    msg = "Solución óptima encontrada" if success else (
        f"Límite de nodos alcanzado ({max_nodes})" if expanded_count >= max_nodes else "No existe solución"
    )

    return SearchResult(
        algorithm_name="Búsqueda A*",
        initial_state=initial_state,
        goal_state=goal_state,
        root_node=root_node,
        goal_node=goal_node,
        expanded_count=expanded_count,
        generated_count=generated_count,
        execution_time_ms=elapsed_ms,
        max_frontier_size=max_frontier_size,
        step_events=step_events,
        success=success,
        message=msg
    )
