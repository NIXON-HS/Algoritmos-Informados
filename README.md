# 🧩 8-Puzzle Solver: Búsqueda Informada (Heurística de Manhattan)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-brightgreen.svg)](https://docs.python.org/3/library/tkinter.html)
[![Algorithm](https://img.shields.io/badge/Algoritmos-Voraz%20%7C%20A*-orange.svg)]()
[![Heuristic](https://img.shields.io/badge/Heur%C3%ADstica-Manhattan%20Distance-purple.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Aplicación de escritorio interactiva desarrollada en **Python (Tkinter)** para la resolución del clásico problema del **8-Puzzle** (tablero de $3 \times 3$) mediante algoritmos de **búsqueda informada (heurística)**. Implementa y compara la **Búsqueda Voraz Primero el Mejor (Greedy Best-First Search)** y la **Búsqueda A\*** utilizando la **Distancia de Manhattan** como heurística admisible y consistente, junto con una visualización jerárquica del **árbol de búsqueda** optimizada para alto rendimiento.

---

## 📸 Vista General de la Interfaz

```text
+------------------------------------------+--------------------------------------------------------+
| PANEL IZQUIERDO (Control & 8-Puzzle)    | PANEL DERECHO (Árbol de Búsqueda Jerárquico)           |
+------------------------------------------+--------------------------------------------------------+
| 1. Selector de Algoritmo                 | Controles: [＋] [－] [🔍 Ajustar Vista]                |
|    ( ) Voraz [f(n) = h(n)]               |                                                        |
|    (•) A*    [f(n) = g(n) + h(n)]        |                     [ #1 • Inicio ]                    |
|                                          |                      | f=24 g:0 h:24 |                 |
| 2. Tablero 8-Puzzle Interactivo          |                             │                          |
|    [ 1 ][ 2 ][ 3 ]                       |                      ▼ Abajo                           |
|    [ 4 ][ 5 ][ 6 ]                       |                     [ #2 • Abajo  ]                    |
|    [ 7 ][ 8 ][ · ]                       |                      | f=24 g:1 h:23 |                 |
|    [🎲 Revolver] [✏️ Ingresar] [🎯 Meta] |                      /             \                   |
|                                          |              ◀ Izq                 ▶ Der               |
| 3. Ejecución del Algoritmo               |        [ #3 • Izq   ]         [ #4 • Der   ]           |
|    [ ⚡ Resolver con A* ]                |                                                        |
|                                          | Leyenda:                                               |
| 4. Métricas de Evaluación                |  🟣 Inicio  🟢 Solución  🔵 Explorado  ⚪ Frontera     |
|    [ h(n) ]   [ g(n) ]   [ f(n) ]        |                                                        |
|    Nodos Expandidos / Generados / Tiempo | • Navegación con arrastre (Pan) y Zoom suave a 60 FPS  |
+------------------------------------------+--------------------------------------------------------+
```

---

## 🏛️ Arquitectura y Separación de Responsabilidades

El proyecto sigue una arquitectura desacoplada donde la lógica matemática del problema es completamente independiente de la interfaz gráfica:

```text
Algoritmos Informados/
├── logic/                      # 🧠 LÓGICA Y ALGORITMOS DEL PROBLEMA
│   ├── __init__.py             # Exportaciones del módulo logic
│   ├── puzzle_state.py         # Modelo de estado 3x3, cálculo de Manhattan, paridad de inversiones
│   ├── node.py                 # Nodo del árbol (estado, costos g, h, f, padre, id, solución)
│   └── search_algorithms.py    # Algoritmos de Búsqueda Voraz y A* con métricas de rendimiento
├── gui/                        # 🎨 INTERFAZ GRÁFICA DE USUARIO (GUI)
│   ├── __init__.py             # Exportaciones del módulo gui
│   ├── puzzle_view.py          # Tablero 3x3 interactivo (clics directos, colores y estados)
│   ├── tree_view.py            # Árbol de búsqueda jerárquico con Frustum Culling y Zoom/Pan
│   └── app.py                  # Ventana principal integradora y orquestadora
├── .gitignore                  # Archivos ignorados por Git
├── main.py                     # Punto de entrada de la aplicación
└── README.md                   # Documentación técnica completa
```

---

## 📐 Fundamentos Teóricos y Matemáticos

### 1. Heurística de la Distancia de Manhattan ($h(n)$)
Para cada ficha numerada $v \in \{1, 2, \dots, 8\}$, su distancia de Manhattan es la suma de las distancias horizontales y verticales desde su posición actual $(x_v, y_v)$ hasta su posición objetivo $(x_v^*, y_v^*)$ (el espacio en blanco $0$ no se contabiliza):

$$h(n) = \sum_{v=1}^{8} \left( |x_v - x_v^*| + |y_v - y_v^*| \right)$$

- **Admisibilidad**: $h(n) \le h^*(n)$ (nunca sobrestima el costo real para alcanzar la meta).
- **Consistencia / Monotonía**: $h(n) \le c(n, a, n') + h(n')$ (cumple la desigualdad triangular).

---

### 2. Comparativa de Algoritmos

| Criterio | Búsqueda Voraz Primero el Mejor | Búsqueda A\* (A-Star) |
| :--- | :--- | :--- |
| **Función de Evaluación** | $f(n) = h(n)$ | $f(n) = g(n) + h(n)$ |
| **Costo Acumulado $g(n)$** | Ignorado | Considerado (profundidad / número de pasos) |
| **Garantía de Optimalidad** | ❌ No garantiza el camino más corto | ✅ **Garantiza la solución óptima** |
| **Completitud** | ✅ Sí (con detección de ciclos) | ✅ Sí |
| **Estrategia** | Expande el nodo que parece más cercano a la meta | Equilibra el costo real incurrido y la estimación restante |

---

### 3. Solubilidad y Paridad de Inversiones
En el 8-Puzzle sobre una cuadrícula impar de $3 \times 3$, no todas las permutaciones iniciales tienen solución matemática. Un estado es alcanzable hacia el objetivo si y solo si el número de **inversiones** tiene la misma paridad (par/impar) que el estado objetivo:

$$\text{Inversión}: \text{Existe un par } (i, j) \text{ tal que } i < j \text{ y } \text{ficha}[i] > \text{ficha}[j] \quad (\text{con } \text{ficha} \ne 0)$$

$$\text{Soluble} \iff (\text{inversiones}(S_{\text{inicial}}) \pmod 2) = (\text{inversiones}(S_{\text{meta}}) \pmod 2)$$

---

## ⚡ Optimizaciones Gráficas de Alto Rendimiento

- **Viewport Frustum Culling**: El visualizador del árbol descarta en tiempo real cualquier nodo o arista que quede fuera del área visible del canvas, permitiendo navegar árboles con miles de nodos a **60 FPS fluidos**.
- **Poda Jerárquica de Subárboles**: Cálculo de *Bounding Boxes* por subárbol para omitir ramas completas en $O(1)$.
- **Diseño de Tarjetas**: Cada nodo muestra el número de identificación, acción realizada, un mini-tablero coloreado (verde si la ficha está en su posición meta) y los valores calculados de $f(n), g(n), h(n)$.

---

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.10 o superior instalado.
- Tkinter (incluido por defecto en las instalaciones oficiales de Python en Windows y macOS).

### Clonar el Repositorio
```bash
git clone https://github.com/NIXON-HS/Algoritmos-Informados.git
cd "8-puzzle-informed-search"
```

### Ejecutar la Aplicación
```bash
python main.py
```

---

## 🎮 Guía de Uso

1. **Seleccionar Algoritmo**: Escoge entre **Búsqueda Voraz** ($f = h$) o **Búsqueda A\*** ($f = g + h$) en la parte superior izquierda.
2. **Configurar el Tablero**:
   - Pulsa **`🎲 Revolver`** para generar un estado aleatorio 100% resoluble.
   - Pulsa **`✏️ Ingresar...`** para introducir manualmente cualquier permutación de 9 números (`1 2 3 4 5 6 7 8 0`).
   - Pulsa **`🎯 Meta`** para volver al estado objetivo.
   - O haz **clic directo en las fichas contiguas al espacio vacío** para moverlas interactivamente.
3. **Resolver**: Pulsa **`⚡ Resolver con A* / Voraz`**.
   - El 8-puzzle animará automáticamente el movimiento de las fichas paso a paso.
   - El árbol de búsqueda se desplegará a la derecha con la ruta óptima resaltada en verde esmeralda.
4. **Inspeccionar el Árbol**:
   - Haz **clic y arrastra** para desplazarte (Pan).
   - Usa la **rueda del ratón** o los botones **`＋` / `－`** para hacer zoom.
   - Pulsa **`🔍 Ajustar Vista`** para encajar el árbol completo en pantalla.
   - Haz **clic en cualquier nodo** para sincronizar el tablero y ver su estado exacto.

---

## 📄 Licencia

Este proyecto se encuentra bajo la Licencia [MIT](LICENSE).
