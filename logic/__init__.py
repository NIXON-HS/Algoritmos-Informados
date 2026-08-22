"""
Módulo de lógica para el 8-Puzzle con Heurística de Manhattan.
"""

from .puzzle_state import PuzzleState, DEFAULT_GOAL, DEFAULT_INITIAL, PRESET_STATES
from .node import Node
from .search_algorithms import greedy_best_first_search, a_star_search, SearchResult

__all__ = [
    "PuzzleState",
    "DEFAULT_GOAL",
    "DEFAULT_INITIAL",
    "PRESET_STATES",
    "Node",
    "greedy_best_first_search",
    "a_star_search",
    "SearchResult"
]
