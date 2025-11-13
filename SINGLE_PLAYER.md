# Single-Player Mode (IA Minimax)

## Descripción

El modo single-player permite jugar contra una IA prácticamente imbatible implementada con el algoritmo **Minimax** con poda **Alpha-Beta**.

## Cómo Jugar

1. **Selecciona el modo**: En la pantalla principal, haz clic en "Single-Player (IA)"
2. **Elige dificultad**:
   - **Difícil (Hard)**: IA usa algoritmo Minimax puro - casi imposible de vencer
   - **Media (Medium)**: IA usa 70% Minimax, 30% movimientos aleatorios - beatable
   - **Fácil (Easy)**: IA elige movimientos al azar - fácil de vencer
3. **Inicia el juego**: Haz clic en "Iniciar Juego vs IA"
4. **Juega**: Eres X y comienzas primero. Haz clic en una celda vacía para jugar

## Sistema de Puntuación

Se mantiene un contador de victorias:
- **X (Tú)**: Número de rondas ganadas
- **O (IA)**: Número de rondas ganadas por la IA

Puedes reiniciar la serie completa con el botón "Reiniciar Match".

## Algoritmo Minimax

### ¿Cómo funciona?

El algoritmo Minimax evalúa **recursivamente** todos los posibles estados del tablero:

1. **Maximizador (IA)**: Busca el movimiento que maximiza su score
2. **Minimizador (Jugador)**: Se asume que el jugador elige el movimiento que minimiza el score de la IA
3. **Evaluación**: 
   - +10: Victoria de la IA (menos la profundidad para preferir victorias rápidas)
   - -10: Victoria del jugador
   - 0: Empate

### Complejidad

- **Tiempo**: O(b^d) donde b es factor de ramificación (~9 primeros movimientos) y d es profundidad
- **Espacio**: O(d) para el stack de recursión
- **Con poda Alpha-Beta**: Reduce significativamente el número de nodos evaluados

### Poda Alpha-Beta

Optimización que "poda" ramas que no pueden afectar el resultado final:
- **Alpha**: Mejor score para el maximizador
- **Beta**: Mejor score para el minimizador
- Si Beta ≤ Alpha, la rama se descarta

### Profundidad

Máximo 9 movimientos (tablero vacío), pero en práctica:
- Primer turno: ~9 opciones
- Turno 2: ~8 opciones
- ... y así sucesivamente

Esto hace que algunos turnos sean casi instantáneos, mientras que el primer movimiento puede ser ligeramente más lento.

## Rendimiento

### Estadísticas de Evaluación

El módulo trackea:
- **nodes_evaluated**: Número de nodos visitados
- **pruned_nodes**: Número de nodos eliminados por poda Alpha-Beta

Ejemplo:
```
Tablero vacío (turno 1):
- Nodes evaluated: ~5000-10000 (sin poda sería 9!)
- Pruned nodes: ~3000-5000 (poda elimina 30-50% de ramas)
```

## Arquitectura

### Backend (Python)

```
server/ai/minimax.py
├── MiniMaxAI (clase principal)
│   ├── find_best_move(board) → (row, col)
│   ├── get_difficulty_move(board, difficulty) → (row, col)
│   ├── _minimax(board, depth, is_maximizing, alpha, beta) → int
│   ├── _check_winner(board) → str | None
│   └── _has_empty_cell(board) → bool
└── AIPlayer (enum)
    ├── COMPUTER = "O"
    └── HUMAN = "X"

server/models/game_manager.py
├── create_single_player_game() → dict
├── handle_single_player_move(game_id, position) → dict
├── get_ai_move(game_id, difficulty) → dict
├── reset_single_player_game(game_id) → dict
└── reset_single_player_match(game_id) → dict
```

### Frontend (JavaScript)

```
client/js/sp.js
└── SinglePlayerGame (clase)
    ├── startGame(difficulty) → Promise
    ├── makeMove(row, col) → Promise
    ├── resetRound() → Promise
    ├── resetMatch() → Promise
    └── getBoard(), getWins(), isActive()

client/js/main.js
├── sendMoveSinglePlayer(row, col)
├── updateWinsSinglePlayer()
└── Manejadores de eventos UI
```

### Endpoints REST

```
POST /api/single-player/game
└── Crea nuevo juego vs IA
    Response: {gameId, board, turn, wins}

POST /api/single-player/{game_id}/move
├── Realiza movimiento humano
├── IA responde automáticamente
└── Response: {board, winner?, draw?, wins, turn?}

POST /api/single-player/{game_id}/reset
└── Reinicia ronda actual

POST /api/single-player/{game_id}/reset-match
└── Reinicia contador de wins (match)
```

## Dificultades Técnicas Resueltas

### 1. Profundidad Infinita
**Problema**: Recursión sin fin en juegos largos
**Solución**: Límite de profundidad en `max_depth=9` (tablero completo)

### 2. Rendimiento en Primer Turno
**Problema**: 9! posibilidades (362,880 nodos sin poda)
**Solución**: Poda Alpha-Beta reduce a ~5,000-10,000 nodos

### 3. Preferencia de Victorias Rápidas
**Problema**: IA prefería ganar lentamente (más movimientos = más "oportunidades" de perder)
**Solución**: Score = `10 - depth` (gana si score > 0, y más rápido es mejor)

### 4. Integración con Juego Best-of-5
**Problema**: IA debe resetear entre rondas pero mantener estado de match
**Solución**: `reset_single_player_round()` limpia tablero pero no `wins`

## Testing

Ver `TESTING.md` para instrucciones de ejecución de tests.

```bash
# Tests para IA
pytest tests/test_minimax.py -v

# Con cobertura
pytest tests/test_minimax.py --cov=ai/minimax --cov-report=html
```

### Casos Cubiertos

- ✅ Inicialización con valores por defecto y personalizados
- ✅ Detección de ganador (horizontal, vertical, diagonales)
- ✅ Detección de tablero vacío
- ✅ Selección de mejor movimiento
- ✅ Bloqueo de victoria del oponente
- ✅ Completación de propia victoria
- ✅ Dificultades (easy, medium, hard)
- ✅ Métricas de eficiencia (nodes evaluated, pruned)
- ✅ Estado del tablero no modificado tras búsqueda
- ✅ Enum AIPlayer

## Limitaciones Conocidas

1. **Primer movimiento**: Puede ser ligeramente lento (1-2 segundos) en hardware débil
2. **No aprende**: Cada juego es independiente (sin machine learning)
3. **Determinista**: Mismo tablero siempre genera mismo movimiento (excepto dificultad medium/easy con aleatoriedad)
4. **No ve futuros lejanos**: Limitado a profundidad 9 (el mínimo necesario para Tic-Tac-Toe)

## Mejoras Futuras

1. **Caché de posiciones**: Guardar scores evaluados para reutilizar
2. **Transposition Tables**: Reconocer tableros equivalentes
3. **Opening Book**: Movimientos predeterminados para apertura
4. **Neural Networks**: Entrenamiento con TensorFlow para aproximar minimax
5. **Modo cooperativo**: Jugar como X+O vs otro jugador

## Referencias

- Algoritmo Minimax: https://en.wikipedia.org/wiki/Minimax
- Poda Alpha-Beta: https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning
- Complejidad de Tic-Tac-Toe: https://en.wikipedia.org/wiki/Tic-tac-toe

## Archivos

- `server/ai/minimax.py` - Implementación del algoritmo (270+ líneas)
- `server/tests/test_minimax.py` - Suite completa de tests (320+ líneas)
- `client/js/sp.js` - Cliente para single-player (180+ líneas)
- `server/main.py` - Endpoints REST para single-player (40+ líneas)
