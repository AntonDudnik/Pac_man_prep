# Предложения по рефакторингу архитектуры

**Дата:** 2026-09-09 · **Коммит:** `f2c7dd7` (ghosts AI logic implementation)
**Состояние на момент анализа:** `make test` — 48 passed; `make lint` — **20 ошибок mypy** (правило Makefile «mandatory lint» не проходит).

---

## 1. Текущая карта модулей

```
pac-man.py                 точка входа (27 строк)
pacman/
  config.py                Pydantic GameConfig / LevelConfig + парсер JSON с комментариями
  engine.py     309 строк  ⚠️ god-object: состояние + ввод + правила + рендер-вызовы + game loop
  ui.py         266 строк  PygameUI: окно, HUD, доска, меню, оверлеи
  spritesheet.py           SpriteSheet (нарезка+кэш) + AnimationManager (кадры)
  highscore.py    0 строк  пустой файл
  adapters/maze.py         MazeAdapter: mazegenerator → битовая сетка + пеллеты + ghost house
  ai/
    ghost_manager.py       оркестрация призраков: волны, режимы, выбор направления
    targeting.py           чистые функции целеуказания (Blinky/Pinky/Inky/Clyde)
    ghost_house.py         очередь выпуска призраков из дома
    wave_timer.py          таймер Scatter/Chase
  entities/
    base.py                Direction, Vector2D, BaseEntity, can_move()
    ghost.py / player.py / state.py (GameState, GhostMode, GhostType, CellType)
```

Базовое разделение (config / entities / ai / adapters / ui) — **правильное и его надо сохранить**.
Проблемы ниже — не в структуре папок, а в том, что слои протекают друг в друга и состояние продублировано.

---

## 2. Ключевые проблемы

### P1. Захардкоженные координаты спавна вместо данных из лабиринта 🔴 критично

Координаты дома призраков и спавна игрока лежат **в шести местах одновременно**:

| Где | Что |
|---|---|
| `engine.py:42` | `Player(position=Vector2D(x=9.0, y=15.0))` |
| `engine.py:46-69` | позиции 4 призраков `(9,8) (9,10) (8,10) (10,10)` |
| `engine.py:267-272` | те же позиции ещё раз в `reset_positions()` |
| `ai/ghost_house.py:33-46` | те же позиции в третий раз в `_setup_initial_positions()` |
| `ai/targeting.py:15-16` | `GHOST_HOUSE_DOOR = (9,8)`, `GHOST_HOUSE_SPAWN = (9,10)` |
| `ai/targeting.py:33` | ещё и дефолтный аргумент `ghost_house_exit=Vector2D(x=9.0, y=8.0)` |

При этом `MazeAdapter._carve_ghost_house_and_spawns()` (`adapters/maze.py:33`) **вычисляет**
дом от центра сетки — и результат никто не читает (`self.player_spawn` не используется нигде).

**Проверено на реальном `config.json` (30×20):**

```
Maze Generated: 30x20 tile grid
Дом призраков вырезан в центре ...... (15, 10)
Призраки при этом спавнятся в ....... (9, 8) / (9, 10)   ← в стене, вне дома
Игрок спавнится в .................... (9, 15)            ← произвольная клетка
maze_adapter.player_spawn (не исп.) .. (15, 13)
Цель «съеденных глаз» ................ (9, 8)             ← ведёт в никуда
Scatter-углы ......................... (17,-2) (18,21)     ← за пределами 30×20
```

То есть игра корректна ровно для одного размера сетки 19×21, а конфиг разрешает любой.

**Решение.** Ввести `MazeLayout` — единственный источник геометрии, который возвращает адаптер:

```python
# pacman/adapters/maze.py
@dataclass(frozen=True)
class MazeLayout:
    grid: list[list[int]]
    width: int
    height: int
    player_spawn: Vector2D
    ghost_house_door: Vector2D          # клетка над воротами
    ghost_house_slots: dict[GhostType, Vector2D]
    scatter_corners: dict[GhostType, Vector2D]   # вычисляются от width/height
```

Дальше `GhostManager`, `GhostHouseManager`, `targeting` и `GameEngine` получают `layout`
в конструкторе, а модульные константы `GHOST_HOUSE_DOOR` / `GHOST_HOUSE_SPAWN` /
`DEFAULT_SCATTER_CORNERS` удаляются.

---

### P2. `GameEngine` — god-object на 309 строк 🔴

Один класс отвечает за: хранение состояния, разбор клавиш, FSM меню, правила поедания,
коллизии, начисление очков, respawn, порядок рендера и главный цикл.

**Симптомы прямо в коде:**
- `handle_input()` (`engine.py:90-110`) — **мёртвый код**: никто не вызывает, дублирует
  ветку меню из `handle_events()`, и обращается к несуществующему `self.running`
  (`engine.py:102, 110`) → при вызове был бы `AttributeError`.
- `self.state = GameState.MENU` присваивается дважды (`engine.py:20` и `:33`).
- `handle_events()` — 80-строчная лестница `if/elif` с четырьмя вложенными уровнями
  логики состояний.
- Docstring `"""Main game state tick..."""` стоит **после** кода (`engine.py:203`).

**Решение — разбить на 4 роли:**

```
GameEngine (≈60 строк)   владеет loop-ом, дёргает InputHandler → World.update → Renderer
InputHandler             pygame.event → GameCommand (перечисление намерений)
World / GameSession      правила: движение, поедание, коллизии, очки, жизни, respawn
Renderer                 порядок отрисовки по состоянию (уже почти есть в PygameUI)
```

Ключ — `InputHandler` возвращает **намерения**, а не мутирует движок:

```python
class GameCommand(Enum):
    MOVE_UP; MOVE_DOWN; MOVE_LEFT; MOVE_RIGHT
    CONFIRM; CANCEL; PAUSE; QUIT
    MENU_UP; MENU_DOWN
    CHEAT_INVINCIBLE; CHEAT_FREEZE; CHEAT_SPEED; DEBUG_FRIGHTEN; ...

KEYMAP: dict[int, GameCommand] = {pygame.K_UP: GameCommand.MOVE_UP, pygame.K_w: ..., }
```

Это сразу даёт: тестируемость без pygame, переназначение клавиш из конфига,
и исчезновение дублирования между `handle_input` и `handle_events`.

Переходы состояний вынести в таблицу вместо лестницы `elif`:

```python
TRANSITIONS: dict[tuple[GameState, GameCommand], GameState] = {
    (GameState.PLAYING, GameCommand.PAUSE):   GameState.PAUSED,
    (GameState.PAUSED,  GameCommand.PAUSE):   GameState.PLAYING,
    (GameState.PLAYING, GameCommand.QUIT):    GameState.CONFIRM_QUIT,
    ...
}
```

---

### P3. Конфиг загружается, но почти не применяется 🔴

`grep "config\." pacman/engine.py` даёт всего 6 обращений. **Не используется:**

| Поле конфига | Что вместо него | Где |
|---|---|---|
| `player_speed` (7.0) | литерал `5.0` | `engine.py:42` |
| `ghost_speed` (6.0) | литерал `4.0` | `engine.py:51,57,63,69` |
| `points_per_pacgum` | литерал `10` | `engine.py:237` |
| `points_per_super_pacgum` | литерал `50` | `engine.py:233` |
| `points_per_ghost` | литерал `200` | `ai/ghost_manager.py:91` |
| `lives` | `self.lives` пишется, но правила читают `self.player.lives` | `engine.py:31` vs `:254` |
| `pacgum` | не читается вообще | `MazeAdapter` сыпет точки на все клетки |
| `levels[]` | не читается вообще | `LevelConfig` — мёртвая модель |
| `highscore_filename` | не читается | `highscore.py` пуст |

Плюс магические числа не из конфига: длительность frightened `7.0`
(`engine.py:234`, `ghost_manager.py:78`), скорость глаз `8.0` и возврат к `4.0`
(`ghost_manager.py:113,118`), пороги выпуска призраков `0/30/60` (`ghost_house.py:10-14`),
расписание волн (`wave_timer.py:17-28`).

**Решение.**
1. Всё, что сейчас литерал, — тянуть из `GameConfig`; правило: **ни одного числового
   литерала правил игры вне `config.py` / `MazeLayout`**.
2. `GameConfig` расширить блоками `GhostTuning` (скорости по режимам, frightened,
   пороги дома, расписание волн) и `ScoreRules`.
3. Реализовать наконец слияние `levels[i]` поверх глобальных значений:
   `effective = base.model_copy(update=level.model_dump(exclude_unset=True))` — это
   именно та задача, ради которой `LevelConfig` и заводился.
4. Убрать дубль `self.lives` / `self.player.lives` — оставить один источник (в `World`).

---

### P4. `is_in_house` — атрибут-призрак, наводимый снаружи 🟠

`Ghost.__init__` не объявляет `is_in_house`. Его создаёт `GhostHouseManager`
присваиванием извне (`ghost_house.py:34,38,42,46`). Следствия:

- `mypy` даёт **6 ошибок** `"Ghost" has no attribute "is_in_house"`;
- `Ghost(ghost_id=9, home_corner=Vector2D())` без менеджера — объект **без атрибута**,
  любое чтение падает;
- флаг **никто не соблюдает**: `GhostManager.update()` двигает призрака независимо от
  `is_in_house`, то есть «запертые» призраки свободно бегают по лабиринту, а
  `_release_ghost()` просто телепортирует их к двери.

**Решение.** Ввести явный режим вместо булева флага-приписки:

```python
class GhostMode(Enum):
    IN_HOUSE = auto()     # ← новый
    LEAVING_HOUSE = auto()# ← новый, путь до двери
    SCATTER = auto()
    CHASE = auto()
    FRIGHTENED = auto()
    EATEN = auto()
```

`GhostManager` получает `match ghost.mode` с одной веткой на режим; `IN_HOUSE` — покачивание
вверх-вниз в доме, `LEAVING_HOUSE` — движение к `layout.ghost_house_door`. Атрибут
`is_in_house` удаляется, `GhostHouseManager` только переключает режим.

---

### P5. Чит-хоткеи F/E/C молча не работают 🟠

```python
# engine.py:173-182
for ghost in self.ghosts:          # self.ghosts — dict[GhostType, Ghost]
    ghost.mode = GhostMode.FRIGHTENED   # ghost — это GhostType, а не Ghost
```

Итерация по `dict` даёт **ключи**. `GhostType` — `str`-Enum, и присваивание атрибута его
члену Python **не запрещает** — исключения нет, но настоящие призраки не меняются.
Проверено: код отрабатывает без ошибок и без эффекта. `mypy` это ловит (5 ошибок
`"GhostType" has no attribute "mode"`) — но `make lint` сейчас всё равно красный, поэтому
сигнал утонул.

Нужен `.values()`, а лучше — метод `GhostManager.force_mode(mode)`, чтобы движок вообще
не трогал внутренности призраков.

---

### P6. `GAME_OVER` — состояние-тупик 🟠

`render()` (`engine.py:280-297`) обрабатывает `MENU` и `PLAYING/PAUSED/CONFIRM_QUIT`.
Для `GAME_OVER` не рисуется ничего (экран замирает на последнем кадре), а в
`handle_events()` клавиши `Q`/`ESC` обрабатываются только для `PLAYING/PAUSED/MENU` —
из `GAME_OVER` **нельзя выйти иначе как закрыв окно**.

Попасть туда легко: `time_remaining <= 0` (`engine.py:200`) или потеря всех жизней
(`engine.py:256`).

**Решение.** Реестр экранов вместо цепочки `if`:

```python
SCREENS: dict[GameState, Screen] = {
    GameState.MENU: MenuScreen(), GameState.PLAYING: GameScreen(),
    GameState.GAME_OVER: GameOverScreen(), ...
}
```
Каждый `Screen` умеет `draw(ui, world)` и `handle(cmd) -> GameState | None`. Забыть
состояние станет невозможно — словарь покрывается тестом `set(SCREENS) == set(GameState)`.

---

### P7. Таймер уровня тикает в меню и на паузе 🟠

```python
def update(self, dt):
    self.ui.update_anim_timer(dt)
    self.time_remaining -= dt              # ← до проверки состояния
    if self.time_remaining <= 0:
        self.state = GameState.GAME_OVER
    if self.state != GameState.PLAYING:    # ← проверка ниже
        return
```

Пока игрок читает меню, `time_remaining` уходит в минус, и игра стартует сразу в
`GAME_OVER` (из которого, по P6, не выйти). Ранний выход должен стоять первым,
а анимационный таймер UI обновляться отдельно от игровой логики.

---

### P8. `dt` фиксирован — логика не привязана к реальному времени 🟡

```python
# engine.py:299-307
fps = 60
dt = 1.0 / fps          # константа
while running: ...
```

`present()` вызывает `clock.tick(60)`, то есть кадры **ограничены** сверху, но при
просадке ниже 60 FPS игра замедляется в реальном времени. Нужно
`dt = self.ui.clock.tick(fps) / 1000.0` с клампом (`min(dt, 0.05)`), чтобы одна
залипшая отрисовка не протаскивала сущность сквозь стену.

---

### P9. `Ghost.update()` — мёртвый дубль ИИ 🟡

`entities/ghost.py:22-42` содержит собственный алгоритм: списание `frightened_timer`
и **случайный** выбор направления на перекрёстке. Движок его не вызывает — работает
`GhostManager.update()`, который делает то же самое (`ghost_manager.py:43-47`,
`:132-141`) плюс настоящее целеуказание. Два расходящихся источника правды: если кто-то
позовёт `ghost.update()`, призраки поедут случайно.

**Решение.** Удалить `Ghost.update()`. `Ghost` должен остаться **данными** (позиция,
режим, таймеры), вся логика — в `ai/`. Заодно удалить `home_corner`: он записывается
в конструкторе (`engine.py:48,54,60,66`), но **не читается нигде** — scatter использует
`DEFAULT_SCATTER_CORNERS`.

---

### P10. `CellType` смешивает три разных понятия 🟡

```python
class CellType(IntEnum):
    NORTH=1; EAST=2; SOUTH=4; WEST=8      # геометрия стен  (статично)
    DOT=16; SUPER_DOT=32                  # содержимое клетки (мутирует в рантайме)
    GHOST_HOUSE=64; GATE=128              # зонирование      (статично)
```

Из-за этого доска — `list[list[int]]`, которую движок правит побитово прямо в правилах
(`engine.py:232,236`), а UI знает о битах (`ui.py:99-140`). Появляется магия вроде
`cell != 15` / `(cell & 15) == 15` (`maze.py:61`, `ui.py:107`) — «сплошной блок».

**Решение.** Разделить на `Wall` (стены+зоны, неизменяемо) и `Pellet`
(`NONE/DOT/SUPER`, изменяемо), и завернуть в класс `Board`:

```python
class Board:
    def walls_at(self, x, y) -> int: ...
    def can_pass(self, x, y, direction, *, is_ghost) -> bool: ...
    def take_pellet(self, x, y) -> Pellet: ...      # мутация только здесь
    @property
    def pellets_left(self) -> int: ...              # даст условие победы, которого нет
    def is_solid(self, x, y) -> bool: ...           # вместо `== 15`
```

Побочный бонус: сейчас **нет условия победы** — уровень не завершается по съеденным
точкам, только по таймеру. `pellets_left == 0` закрывает эту дыру.

---

### P11. Проверка стен идёт по клетке-источнику, а не по цели 🟡

`can_move()` (`entities/base.py:94-128`) читает биты **текущей** клетки. Для стен это
работает (биты дублируются с обеих сторон), но ворота дома дырявые: игрок, стоящий
*над* воротами и идущий `DOWN`, проверяет свою клетку — `GATE`-бита там нет, — и
спокойно входит в дом призраков. Проверять надо клетку назначения (`x+dx, y+dy`), либо
явно оба конца перехода. Логике место в `Board.can_pass()` (см. P10).

---

### P12. `make lint` красный — 20 ошибок mypy 🟠

Правило в `Makefile` названо «mandatory lint», но не проходит:

| Файл | Ошибок | Причина |
|---|---|---|
| `entities/state.py:28-35` | 8 | `NORTH: int = 1` — аннотированные члены Enum запрещены |
| `ai/ghost_house.py` | 6 | `is_in_house` (см. P4) |
| `engine.py:174-182` | 5 | итерация по ключам dict (см. P5) |
| `ai/targeting.py:81` | 1 | `can_move_fn` без аннотации |
| `adapters/maze.py:24`, `ai/ghost_manager.py:93` | 2 | `Returning Any` |

Первые три группы — не косметика, а **настоящие баги, которые mypy уже нашёл**.
Чинить надо сразу, иначе инструмент бесполезен. Для `can_move_fn` — `Protocol`:

```python
class CanMoveFn(Protocol):
    def __call__(self, board: list[list[int]], grid_x: int, grid_y: int,
                 direction: Direction, is_ghost: bool = False) -> bool: ...
```

---

### P13. Мелочи по слоям 🟢

- **`pac-man.py:15-23`** — закомментированный `try/except` блоком `'''...'''`. Удалить;
  обработку ошибок сделать явной (задача «zero traceback audit» из roadmap Phase 6).
- **`os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]` + `# noqa: E402`** повторяется в
  `engine.py:11-14` и `ui.py:8-9`. Вынести в `pacman/platform.py`, импортируемый первым,
  и убрать `ignore = ["E402"]` из `pyproject.toml`.
- **`engine.py` импортирует `pygame`** только ради типа события. После P2 (InputHandler)
  ядро игры перестаёт зависеть от pygame вообще — тесты правил пойдут без `SDL_VIDEODRIVER`.
- **`ui.py:154-177`, `draw_ghosts`** — защитное `getattr(self, "animations", None) or
  getattr(self, "anim_manager", None)` и `Union[Dict, List]` в сигнатуре: следы старых
  версий API. Зафиксировать один контракт.
- **`ui.py:216`** — изменяемый список как значение по умолчанию
  (`options: list[str] = ["PLAY GAME", ...]`). Классическая ловушка Python.
- **`ui.py:182`** — `top_offset = 40` вместо готовой константы `HUD_HEIGHT`.
- **`MazeAdapter._carve_ghost_house_and_spawns()`** — метод «вырезает» и **попутно**
  присваивает `self.player_spawn`. Побочный эффект в имени не отражён; после P1 это
  становится честным возвратом в `MazeLayout`.
- **`highscore.py`** пуст, а `GameConfig.highscore_filename` есть — либо реализовать
  (Phase 5 roadmap), либо удалить файл.
- **`README.md`** пуст.

---

## 3. Целевая архитектура

```
                    ┌──────────────────────────┐
   config.json ───► │ config.py  GameConfig    │  все числа правил
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ adapters/maze.py         │  mazegenerator → MazeLayout
                    │   → MazeLayout           │  (grid + ВСЕ координаты)
                    └────────────┬─────────────┘
                                 ▼
┌───────────────┐   ┌──────────────────────────┐   ┌────────────────────┐
│ InputHandler  │──►│ World / GameSession      │──►│ Renderer + PygameUI│
│ keys→Command  │   │ правила, очки, коллизии  │   │ Screen-реестр      │
└───────────────┘   │   ├─ Board (пеллеты)     │   └────────────────────┘
                    │   ├─ Player  (данные)    │
                    │   ├─ Ghost×4 (данные)    │
                    │   └─ GhostManager (ИИ)   │
                    └────────────┬─────────────┘
                                 ▲
                    ┌────────────┴─────────────┐
                    │ GameEngine ≈60 строк     │  только цикл и dt
                    └──────────────────────────┘
```

**Правила зависимостей, которые надо удерживать:**

1. `entities/` — чистые данные, **не** импортируют `ai/`, `ui/`, `pygame`.
2. `ai/` зависит от `entities/` и `MazeLayout`, **не** от `engine`/`ui`/`pygame`.
3. `ui/` умеет рисовать, но **не** меняет игровое состояние.
4. `engine` знает про всех, но никто не знает про `engine`.
5. `pygame` импортируется **только** в `ui/`, `spritesheet.py` и `input_handler.py`.

Пункт 5 проверяется одним тестом:

```python
def test_core_is_pygame_free():
    import subprocess, pathlib
    core = ["pacman/entities", "pacman/ai", "pacman/adapters", "pacman/config.py"]
    hits = subprocess.run(["grep", "-rn", "import pygame", *core], capture_output=True)
    assert hits.stdout == b""
```

---

## 4. План работ по приоритетам

### Этап A — починить сломанное (0.5 дня, без изменения структуры)

| # | Задача | Файл |
|---|---|---|
| A1 | `for ghost in self.ghosts.values()` — читы F/E/C | `engine.py:173,177,180` |
| A2 | Ранний `return` до списания `time_remaining` | `engine.py:197-204` |
| A3 | Экран и выход для `GAME_OVER` | `engine.py:280,131` |
| A4 | Убрать аннотации у членов `CellType` | `entities/state.py:28-35` |
| A5 | `is_in_house: bool = True` в `Ghost.__init__` (временный фикс до P4) | `entities/ghost.py` |
| A6 | Аннотация `can_move_fn` (Protocol) + два `Returning Any` | `targeting.py`, `maze.py`, `ghost_manager.py` |
| A7 | Удалить мёртвые `handle_input()`, `_execute_menu_selection()`, закомментированный блок в `pac-man.py` | `engine.py:90-110`, `pac-man.py:15-23` |
| A8 | `dt` из `clock.tick()` с клампом | `engine.py:299` |

**Критерий готовности этапа:** `make lint` зелёный, `make test` зелёный.
Дальше — правило: лендинг в `master` только при зелёном `make lint`.

### Этап B — единый источник геометрии (1–1.5 дня) → снимает P1

1. `MazeLayout` (dataclass) + `MazeAdapter.build_layout()`; scatter-углы вычисляются
   из `width/height`, а не константы.
2. `GhostManager`, `GhostHouseManager`, `targeting` принимают `layout` параметром.
3. Удалить `GHOST_HOUSE_DOOR`, `GHOST_HOUSE_SPAWN`, `DEFAULT_SCATTER_CORNERS`,
   `Ghost.home_corner`, дефолт `ghost_house_exit`.
4. `reset_positions()` берёт координаты из `layout` (третий дубль исчезает).
5. **Тест-регрессия:** прогнать 300 кадров на сетках 19×21, 30×20, 41×31 —
   ни один призрак не должен оказаться внутри сплошной клетки.

### Этап C — конфиг реально управляет игрой (0.5–1 день) → снимает P3

1. Протянуть `player_speed`, `ghost_speed`, `points_per_*`, `lives`.
2. Блоки `GhostTuning` / `ScoreRules` в `GameConfig`, вынести туда `7.0`, `8.0`,
   `0/30/60`, расписание волн.
3. Слияние `levels[i]` поверх базового конфига (`model_copy(update=...)`).
4. Убрать дубль `engine.lives` / `player.lives`.

### Этап D — разбор god-object (1.5–2 дня) → снимает P2, P6

1. `input.py`: `GameCommand` + `KEYMAP` + `InputHandler` (тестируется без окна).
2. `screens.py`: реестр `SCREENS` + тест на покрытие всех `GameState`.
3. `world.py`: правила, коллизии, очки, respawn — вынести из `engine.py`.
4. `GameEngine` ужимается до цикла; `import pygame` из него исчезает.

### Этап E — доска и режимы (1 день) → снимает P4, P9, P10, P11

1. Класс `Board` с `can_pass()` по клетке-**назначения**, `take_pellet()`, `pellets_left`.
2. Разделение `CellType` → `Wall` + `Pellet`; убрать магию `15`.
3. `GhostMode.IN_HOUSE` / `LEAVING_HOUSE` вместо `is_in_house`; `match`-диспетчер в `GhostManager`.
4. Удалить `Ghost.update()`.
5. Условие победы: `pellets_left == 0` → `GameState.LEVEL_COMPLETE`.

### Этап F — оставшееся из roadmap (Phase 5–6)

`highscore.py` (или удалить), README/архитектурный обзор, zero-traceback audit.

---

## 5. Что оставить как есть

Это уже сделано хорошо, трогать не нужно:

- **`ai/targeting.py`** — чистые функции без состояния, воспроизводят аркадные баги
  (overflow Pinky при `UP`, приоритет `UP > LEFT > DOWN > RIGHT`). Эталон стиля для
  остального кода; правки — только замена константных углов на `layout`.
- **`ai/wave_timer.py`** — компактный dataclass с одной обязанностью; в конфиг вынести
  расписание, структуру не менять.
- **`spritesheet.py`** — разделение «нарезка+кэш» (`SpriteSheet`) и «кадры анимации»
  (`AnimationManager`) правильное, кэш по ключу палитры рабочий.
- **`config.py`** — Pydantic-валидация и `strip_json_comments` с graceful fallback.
  Не хватает только *применения* результата (Этап C).
- **Структура каталогов** `entities / ai / adapters / ui` — целевая архитектура строится
  внутри неё, переезды файлов не требуются.

---

## 6. Сводная таблица

| # | Проблема | Важность | Этап | Основные файлы |
|---|---|---|---|---|
| P1 | Координаты дома/спавна в 6 местах, игра ломается на любом размере ≠19×21 | 🔴 | B | `engine`, `ghost_house`, `targeting`, `maze` |
| P2 | `GameEngine` — god-object, мёртвый `handle_input` | 🔴 | D | `engine.py` |
| P3 | Конфиг загружается, но не применяется (9 полей) | 🔴 | C | `engine`, `ghost_manager`, `config` |
| P4 | `is_in_house` наводится снаружи и не соблюдается | 🟠 | E | `ghost_house`, `ghost` |
| P5 | Читы F/E/C молча не работают (итерация по ключам) | 🟠 | A | `engine.py:173` |
| P6 | `GAME_OVER` — тупик без экрана и выхода | 🟠 | A/D | `engine.py:280` |
| P7 | Таймер уровня тикает в меню и на паузе | 🟠 | A | `engine.py:199` |
| P8 | Фиксированный `dt`, не привязан к реальному времени | 🟡 | A | `engine.py:302` |
| P9 | `Ghost.update()` — мёртвый дубль ИИ; `home_corner` не читается | 🟡 | E | `entities/ghost.py` |
| P10 | `CellType` смешивает стены/содержимое/зоны; нет условия победы | 🟡 | E | `state`, `maze`, `ui` |
| P11 | `can_move` проверяет клетку-источник → ворота дырявые | 🟡 | E | `entities/base.py:94` |
| P12 | `make lint` красный: 20 ошибок mypy | 🟠 | A | 6 файлов |
| P13 | Мелочи по слоям (pygame-бойлерплейт, mutable default, пустые файлы) | 🟢 | A/F | `ui`, `pac-man.py`, `highscore` |

**Рекомендуемый порядок:** A → B → C → D → E → F.
Этапы A–C дают максимум пользы за ~2 дня и не требуют переписывания; D и E — уже
собственно архитектурная перестройка, и делать их безопасно только после того, как
`make lint` станет зелёным и появится регрессионный тест на разные размеры сетки.
