# Classic Pac-Man Ghost AI & Targeting Specification

## 1. Global Ghost Sub-Tile Movement & Speed Mechanics
* **Base Speeds**:
  * Pac-Man (normal): 100% speed (~5.0 tiles/sec).
  * Pac-Man (eating dots): 90% speed (~4.5 tiles/sec, 1-frame pause per pac-gum eaten).
  * Ghosts (normal): 95% speed (~4.75 tiles/sec).
  * Ghosts (frightened): 50% speed (~2.5 tiles/sec).
  * Blinky (Cruise Elroy Phase 1): 100% speed when pac-gums remaining $\le 20$.
  * Blinky (Cruise Elroy Phase 2): 105% speed when pac-gums remaining $\le 10$.
* **Intersection Decision Logic**:
  * Ghosts NEVER reverse direction $180^\circ$ unless transitioning between states (Chase $\leftrightarrow$ Scatter $\leftrightarrow$ Frightened).
  * At any tile intersection, ghosts look 1 tile ahead to the open path options (UP, DOWN, LEFT, RIGHT) and pick the tile that minimizes the **Euclidean distance squared** ($d^2 = (x_2 - x_1)^2 + (y_2 - y_1)^2$) to their specific target tile.
  * **Tie-Breaker Hierarchy**: UP > LEFT > DOWN > RIGHT.

---

## 2. Character Personality & Target Calculations

### 🔴 Blinky (Red - "Shadow")
* **Role**: Direct Chaser.
* **Target Tile**: Pac-Man's exact current grid coordinate $(P_x, P_y)$.
* **Cruise Elroy**: Speeds up when remaining pac-gums drop below thresholds, ignoring Scatter mode.

### 🌸 Pinky (Pink - "Speedy")
* **Role**: Ambush & Trapper.
* **Target Tile**: 4 tiles ahead of Pac-Man in his current facing direction.
  * *Original Arcade Bug Mirror*: If Pac-Man faces UP, target tile is 4 tiles UP and 4 tiles LEFT: $(P_x - 4, P_y - 4)$. Otherwise, $(P_x + 4 \cdot D_x, P_y + 4 \cdot D_y)$.

### 🩵 Inky (Cyan - "Bashful")
* **Role**: Complex Vector Flanker.
* **Target Calculation**:
  1. Take the tile 2 tiles ahead of Pac-Man: $T_2 = (P_x + 2 \cdot D_x, P_y + 2 \cdot D_y)$.
  2. Construct a vector from Blinky's position $B = (B_x, B_y)$ to $T_2$.
  3. Double that vector: $\vec{Target} = B + 2 \cdot (T_2 - B)$.

### 🟧 Clyde (Orange - "Pokey")
* **Role**: Cowardly / Territory Patrol.
* **Target Calculation**:
  * Calculates distance $D$ to Pac-Man.
  * If $D \ge 8$ tiles: Targets Pac-Man's exact location (chases).
  * If $D < 8$ tiles: Retreats toward his assigned home scatter corner.

---

## 3. Wave System (Chase / Scatter Timers)
Ghosts alternate between **Scatter** (retreating to corners) and **Chase** modes according to a global timer:
* **Scatter 1**: 7 seconds $\rightarrow$ **Chase 1**: 20 seconds
* **Scatter 2**: 7 seconds $\rightarrow$ **Chase 2**: 20 seconds
* **Scatter 3**: 5 seconds $\rightarrow$ **Chase 3**: 20 seconds
* **Scatter 4**: 5 seconds $\rightarrow$ **Chase 4**: Indefinite (Permanent Chase)