# Triqui (Tic-Tac-Toe) - Juego Online en Tiempo Real

Una aplicación web para jugar **Tic-Tac-Toe (Tres en Raya)** en arquitectura cliente-servidor usando WebSocket. Implementa mejor-de-5 (first to 3 wins), persistencia de resultados en leaderboard, y protección contra spam.

## 📋 Características

- ✅ **Juego 1 vs 1 en tiempo real** vía WebSocket
- ✅ **Best-of-5**: El primero en ganar 3 partidas gana la serie
- ✅ **Reconexión automática**: Los jugadores pueden desconectarse y reconectarse
- ✅ **Leaderboard**: Persistencia en JSON o PostgreSQL
- ✅ **Rate-limiting**: Protección contra spam de mensajes
- ✅ **Server es autoridad**: Todas las validaciones en el servidor
- ✅ **Tests**: Suite de tests con pytest para Game y rate-limiter
- ✅ **Patrones de diseño**: Factory, Strategy, Observer, Singleton

## 🏗️ Arquitectura

### Diagrama General

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Cliente)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HTML/CSS/JS (Vanilla)                              │   │
│  │  - Tablero 3x3 (click para mover)                   │   │
│  │  - Indicador de turno                               │   │
│  │  - Botón de reinicio (best-of)                      │   │
│  │  - Mostradores de victorias                         │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │ WebSocket JSON                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ws://localhost:8000/ws          │
        │             │             │
┌───────▼─────────────▼─────────────▼──────────────────────────┐
│               BACKEND (Servidor FastAPI + Uvicorn)           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ main.py                                                │ │
│  │ - WebSocket endpoint (/ws)                            │ │
│  │ - REST endpoints (/leaderboard GET/POST/DELETE)       │ │
│  │ - Startup hook (init DB)                              │ │
│  └────┬───────────────────────────────────────────────┬───┘ │
│       │                                               │     │
│  ┌────▼─────────────────┐  ┌─────────────────────────▼───┐  │
│  │ GameManager          │  │  Leaderboard Module         │  │
│  │ ─────────────────────  │  ─────────────────────────── │  │
│  │ + register_player     │  │ + get_leaderboard()       │  │
│  │ + connect_and_pair    │  │ + add_result()            │  │
│  │ + handle_message      │  │ + clear_leaderboard()     │  │
│  │ + _handle_move        │  │                           │  │
│  │ + _handle_reset_match │  │ Backend: JSON o PostgreSQL│  │
│  │ + _rate_limiter       │  │                           │  │
│  └────┬────────────────┬─┘  └───────────────────────────┘  │
│       │                │                                    │
│  ┌────▼────────────────▼─────┐                            │
│  │  Game                      │                            │
│  │  ────────────────────────  │                            │
│  │  + board (1D, 9 celdas)    │                            │
│  │  + make_move(pos)          │                            │
│  │  + reset()                 │                            │
│  │  + reset_match()           │                            │
│  │  + wins: {"X":int,"O":int} │                            │
│  │  + match_finished: bool    │                            │
│  └─────────────────────────────┘                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Utilidades                                           │ │
│  │ ────────────────────────────────────────────────────  │ │
│  │ - TokenBucketLimiter: Rate-limiting por cliente     │ │
│  │ - MessageType enum: Tipos de mensajes               │ │
│  │ - Factory: Creación de Game/Player                  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└──────────────────────────────────────────────────────────────┘
                      │
                      │ SELECT/INSERT/DELETE
                      ▼
           ┌──────────────────────┐
           │ Leaderboard Storage  │
           │ ──────────────────── │
           │ JSON file (defecto)  │
           │ PostgreSQL (optional)│
           └──────────────────────┘
```

### Flujo de Mensajes WebSocket

#### Conexión Inicial (Join/Resume)

```
Cliente                          Servidor
  │                                │
  │─── {type:"join",               │
  │     playerName:"Alice"} ────────→
  │                                │
  │                                │ [crea Player, registra]
  │                                │
  │ ←────────────────── {type:"registered",
  │                      playerId:"uuid"} 
  │                                │
  │ ←────────────────── {type:"waiting"}
  │                      (esperando rival)
  │
  │                          [Otro cliente se conecta]
  │                                │
  │ ←────────────────── {type:"assigned",
  │                      symbol:"X",
  │                      gameId:"uuid"}
  │
  │ ←────────────────── {type:"state",
  │                      board:[[...]],
  │                      turn:"X",
  │                      wins:{X:0,O:0}}
```

#### Durante la Partida

```
Cliente                          Servidor
  │                                │
  │─── {type:"move",               │
  │     position:[0,0],            │
  │     gameId:"uuid"} ────────────→
  │                                │
  │                                │ [valida: turno, posición]
  │                                │ [aplica movimiento]
  │                                │ [verifica ganador/empate]
  │                                │
  │ ←────────────────── {type:"state",
  │                      board:[[...]],
  │                      turn:"O",
  │                      wins:{X:0,O:0}}
```

#### Fin de Partida y Match Reset

```
Cliente                          Servidor
  │                                │
  │─── {type:"move", ...} ────────→
  │                                │
  │                                │ [X gana: wins={X:1,O:0}]
  │                                │ [Persiste en leaderboard]
  │                                │
  │ ←────────────────── {type:"win",
  │                      winner:"X",
  │                      matchFinished:false}
  │
  │ [Cliente muestra botón "Reiniciar Serie"]
  │
  │─── {type:"reset_match",        │
  │     gameId:"uuid"} ────────────→
  │                                │
  │                                │ [wins={X:0,O:0}]
  │ ←────────────────── {type:"state",
  │                      board:[[...]],
  │                      turn:"X",
  │                      wins:{X:0,O:0}}
```

## 🔧 Tecnologías

### Backend
- **Python 3.8+**
- **FastAPI**: Framework web async
- **Uvicorn**: Servidor ASGI
- **SQLAlchemy**: ORM para Postgres (opcional)
- **asyncpg**: Driver Postgres async
- **pytest**: Testing framework

### Frontend
- **HTML5**
- **CSS3**
- **JavaScript (Vanilla)**
- **WebSocket API** (nativo del navegador)

### Persistencia
- **JSON** (por defecto, sin dependencias)
- **PostgreSQL** (opcional, via SQLAlchemy async)

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.8+
- pip
- (Opcional) PostgreSQL 12+

### Setup Local (JSON leaderboard)

1. **Clonar repositorio**
   ```bash
   git clone <repo-url>
   cd proyecto1
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r server/requirements.txt
   ```

4. **Ejecutar servidor**
   ```bash
   uvicorn server.main:app --reload
   ```
   Servidor estará en `http://127.0.0.1:8000`

5. **Abrir cliente**
   - Navegador: `file:///ruta/a/client/index.html`
   - O usar local server: `python -m http.server 8080 -d client` y acceder a `http://127.0.0.1:8080`

### Setup con PostgreSQL

1. **Crear base de datos**
   ```sql
   CREATE DATABASE triqui;
   CREATE USER triqui_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE triqui TO triqui_user;
   ```

2. **Configurar variable de entorno**
   ```bash
   # .env
   DATABASE_URL=postgresql+asyncpg://triqui_user:secure_password@localhost:5432/triqui
   ```

3. **Ejecutar servidor** (las tablas se crean automáticamente)
   ```bash
   python -m dotenv load
   uvicorn server.main:app --reload
   ```

## 📡 API REST

### Leaderboard

#### GET /leaderboard
Devuelve lista de resultados (más reciente primero)

**Response:**
```json
[
  {
    "id": 1,
    "game_id": "uuid",
    "winner_name": "Alice",
    "loser_name": "Bob",
    "winner_symbol": "X",
    "wins": {"X": 3, "O": 1},
    "timestamp": "2025-11-10T15:30:45Z"
  }
]
```

#### POST /leaderboard
Añadir resultado manualmente (útil para tests)

**Request:**
```json
{
  "game_id": "uuid",
  "winner_name": "Alice",
  "loser_name": "Bob",
  "winner_symbol": "X",
  "wins": {"X": 3, "O": 1}
}
```

#### DELETE /leaderboard
Limpiar leaderboard (testing)

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest server/tests/

# Con coverage
pytest --cov=server server/tests/

# Un archivo específico
pytest server/tests/test_game.py

# Una clase específica
pytest server/tests/test_game.py::TestGame
```

### Suites Disponibles
- `test_game.py`: Lógica del juego (win, draw, best-of-5)
- `test_rate_limiter.py`: Rate-limiting y token bucket

## 🎨 Patrones de Diseño

### 1. **Factory Pattern** (`models/factory.py`)
- **Uso**: `GameFactory.create_game()`, `PlayerConnectionFactory.create_player()`
- **Beneficio**: Centraliza creación de objetos; facilita testing y extensión
- **Donde se aplica**: 
  ```python
  # En GameManager.connect_and_pair():
  game = GameFactory.create_game_with_players(waiting_player.id, player.id)
  ```

### 2. **Strategy Pattern** (`models/game_manager.py`)
- **Uso**: Diferentes handlers para tipos de mensajes
- **Handlers**: `_handle_move`, `_handle_reset_match`, `_handle_chat`
- **Beneficio**: Fácil de extender (agregar nuevos tipos de mensajes)
- **Donde se aplica**:
  ```python
  handlers = {
      MessageType.MOVE: self._handle_move,
      MessageType.RESET_MATCH: self._handle_reset_match,
  }
  ```

### 3. **Observer Pattern** (`models/game_manager.py`)
- **Uso**: Broadcast de estado a ambos jugadores
- **Método**: `_broadcast_game_state()`, `_broadcast_to_game()`
- **Beneficio**: Sincronización automática entre clientes
- **Donde se aplica**:
  ```python
  await self._broadcast_to_game(game, {"type": "state", "board": ...})
  ```

### 4. **Singleton Pattern** (`main.py`)
- **Uso**: Una única instancia de `GameManager` por app
- **Instancia**: `manager = GameManager()` (global)
- **Beneficio**: Estado compartido y consistente de jugadores/partidas
- **Donde se aplica**: Todos los WebSocket endpoints usan el mismo `manager`

### 5. **Decorator/Middleware Pattern** (rate-limiting)
- **Uso**: `TokenBucketLimiter` protege `handle_message`
- **Beneficio**: Protección contra spam sin afectar lógica del juego
- **Donde se aplica**:
  ```python
  if not self._rate_limiter.is_allowed(player.id):
      # Rechazar mensaje
  ```

## 🔒 Seguridad

- ✅ **Server es autoridad**: Todas las validaciones en servidor
- ✅ **Rate-limiting**: Max 10 mensajes/seg por cliente (token bucket)
- ✅ **Validación de entrada**: Posiciones sanitizadas (0-8)
- ✅ **Manejo de desconexiones**: Notificación a otros jugadores
- ⚠️ **CORS**: Abierto en desarrollo (restringir en producción)
- ⚠️ **Auth**: No implementado (recomendado para producción)

## 📝 Requisitos del Proyecto

| Requisito | Estado | Notas |
|-----------|--------|-------|
| Arquitectura cliente-servidor | ✅ | FastAPI + JavaScript |
| Gestión de conexiones | ✅ | Join, resume, desconexión |
| Validar movimientos | ✅ | Server-side, turnos, posiciones |
| Detectar victoria/empate | ✅ | 8 patrones de 3-en-raya |
| Best-of-5 | ✅ | Primero a 3 victorias |
| Sincronización | ✅ | Broadcast en tiempo real |
| Leaderboard | ✅ | JSON + Postgres |
| Rate-limiting | ✅ | Token bucket, 10 msg/seg |
| Patrones de diseño | ✅ | Factory, Strategy, Observer, Singleton |
| SOLID | ⚠️ | Parcialmente (ver notas) |
| Testing | ✅ | pytest + 20+ tests |
| Documentación | ✅ | Docstrings + README + diagrama |

## 📌 SOLID Aplicado

- **S**ingle Responsibility: Cada clase tiene una responsabilidad clara (Game → lógica, GameManager → orchestración, Player → conexión)
- **O**pen/Closed: Handlers estrategy para extensibilidad
- **L**iskov Substitution: (Parcial) PlayerConnection usa interfaz estándar
- **I**nterface Segregation: MessageType enum segregado por dominio
- **D**ependency Inversion: (Parcial) Leaderboard inyectado en GameManager

## 🐛 Próximos Pasos (Optional)

- [ ] Chat UI en cliente (backend listo)
- [ ] IA single-player (minimax)
- [ ] Autenticación (JWT)
- [ ] CI/CD (GitHub Actions)
- [ ] Migración a SQLite/Postgres por defecto
- [ ] Websocket SSL/TLS (WSS)
- [ ] Estadísticas por jugador

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

---

**Autores**: Proyecto Final Arquitectura Cliente-Servidor  
**Fecha**: Noviembre 2025  
**Estado**: ✅ Funcional, tested, documentado
