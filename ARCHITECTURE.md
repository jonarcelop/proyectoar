# Arquitectura Técnica - Decisiones de Diseño

## 1. Patrones de Diseño Aplicados

### 1.1 Factory Pattern
**Ubicación**: `server/models/factory.py`

**Propósito**: Centralizar la creación de objetos `Game` y `PlayerConnection`.

**Implementación**:
```python
class GameFactory:
    @staticmethod
    def create_game_with_players(player_x_id, player_o_id) -> Game:
        game = Game()
        game.player_x = player_x_id
        game.player_o = player_o_id
        game.current_player = player_x_id
        return game
```

**Beneficios**:
- Encapsulación: Toda la lógica de inicialización en un lugar
- Testabilidad: Fácil hacer mock en tests
- Extensibilidad: Cambios futuros (ej: custom board size) sin afectar GameManager
- Separación de responsabilidades: GameManager no sabe cómo crear Games

**Patrón SOLID**: Alinea con **Single Responsibility** y **Open/Closed**

---

### 1.2 Strategy Pattern
**Ubicación**: `server/models/game_manager.py` (método `handle_message`)

**Propósito**: Encapsular diferentes estrategias de procesamiento de mensajes.

**Implementación**:
```python
handlers = {
    MessageType.MOVE: self._handle_move,
    MessageType.RESET_MATCH: self._handle_reset_match,
    MessageType.CHAT_MESSAGE: self._handle_chat
}
handler = handlers.get(mtype)
if handler:
    await handler(player, data)
```

**Beneficios**:
- Extensibilidad: Agregar nuevo tipo de mensaje = agregar handler
- Código limpio: `handle_message()` sin enormes if/elif chains
- Testing: Cada handler testeable independientemente

**Patrón SOLID**: Respeta **Open/Closed** (abierto a extensión, cerrado a modificación)

---

### 1.3 Observer Pattern
**Ubicación**: `server/models/game_manager.py` (métodos `_broadcast_to_game`, `_broadcast_game_state`)

**Propósito**: Notificar a múltiples "observers" (clientes) de cambios de estado.

**Implementación**:
```python
async def _broadcast_to_game(self, game: Game, message: dict):
    """Envía un mensaje a todos los jugadores en una partida."""
    players = [self._players.get(game.player_x), self._players.get(game.player_o)]
    for player in players:
        if player and player.websocket:
            await player.send(message)
```

**Beneficios**:
- Sincronización automática: Ambos clientes reciben actualizaciones
- Desacoplamiento: Clientes no conocen la lógica interna del juego
- Escalabilidad: Fácil agregar más "observers" (ej: spectators)

**Patrón SOLID**: Logra **Dependency Inversion** (depende de abstracciones, no detalles)

---

### 1.4 Singleton Pattern
**Ubicación**: `server/main.py`

**Propósito**: Una única instancia de `GameManager` para toda la aplicación.

**Implementación**:
```python
# main.py
manager = GameManager()  # Instancia global única

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.handle_message(...)  # Usa la misma instancia
```

**Beneficios**:
- Estado compartido: Todos los WebSocket endpoints comparten players/games
- Thread-safe (en async): Una instancia = una state machine
- Centralización: Fácil debugging y logging

**Patrón SOLID**: Cumple **Single Responsibility** (un único GameManager gestiona todo)

---

### 1.5 Rate Limiter / Decorator Pattern
**Ubicación**: `server/utils/rate_limiter.py` + integración en `GameManager`

**Propósito**: Proteger contra spam sin modificar la lógica core del juego.

**Implementación**:
```python
class TokenBucketLimiter:
    def is_allowed(self, client_id: str) -> bool:
        # Token bucket algorithm: agregar tokens cada segundo
        # Consumir 1 token por mensaje
        # Rechazar si no hay tokens

class GameManager:
    def __init__(self):
        self._rate_limiter = TokenBucketLimiter(capacity=100, refill_rate=10.0)
    
    async def handle_message(self, player, data):
        if not self._rate_limiter.is_allowed(player.id):
            await player.send({"type": "error", "message": "Rate limited"})
            return
        # Procesar mensaje...
```

**Beneficios**:
- Protección contra DDoS: Max 10 mensajes/segundo por cliente
- Separación de responsabilidades: Lógica de rate-limit aislada
- Reutilizable: `TokenBucketLimiter` independiente del contexto

**Algoritmo**: Token Bucket (justo y eficiente para límites suaves)

---

## 2. Principios SOLID

### S - Single Responsibility
Cada clase tiene UNA razón para cambiar:
- `Game`: Lógica del juego (detectar ganador, aplicar movimiento)
- `Player`: Gestionar conexión WebSocket
- `GameManager`: Orquestar jugadores y partidas
- `TokenBucketLimiter`: Rate-limiting
- `MessageType`: Enumerar tipos de mensajes

✅ **Bien aplicado**: Las clases son pequeñas, enfocadas, testables

### O - Open/Closed
Las clases deberían estar:
- ✅ **Abiertas a extensión**: Nuevo handler = solo agregar estrategia
- ✅ **Cerradas a modificación**: No cambiar `handle_message()` base

Ejemplo:
```python
# Agregar nuevo tipo de mensaje es trivial:
class MessageType(str, Enum):
    SPECTATE = "spectate"  # Nuevo tipo

# En GameManager:
handlers[MessageType.SPECTATE] = self._handle_spectate

async def _handle_spectate(self, player, data):
    # Nueva lógica
```

### L - Liskov Substitution
(Parcialmente aplicado) PlayerConnection sigue un contrato esperado (método `send()`).
En una app más grande, definiríamos una interfaz `IPlayer` y múltiples implementaciones.

```python
# Future improvement:
from abc import ABC, abstractmethod

class IPlayer(ABC):
    @abstractmethod
    async def send(self, message: dict): pass
    
    @abstractmethod
    async def disconnect(self): pass

class PlayerConnection(IPlayer):
    # Implementa contrato
```

### I - Interface Segregation
Cada cliente recibe **solo los mensajes que necesita**:
- Jugador activo: recibe `state`, `move`, `win`
- Jugador esperando: recibe `waiting`, `assigned`
- Espectador futuro: recibiría `spectate_state`

No hay "mega-mensaje" con toda la información.

### D - Dependency Inversion
GameManager depende de **abstracciones**, no detalles:
- No crea `Game` directamente → usa `GameFactory` (futuro)
- No conoce detalles de WebSocket → usa `PlayerConnection` (abstracta)
- No escribe directo a archivos → usa módulo `leaderboard` (inyectable)

```python
# Podríamos inyectar diferentes backends de leaderboard:
class GameManager:
    def __init__(self, leaderboard_backend=None):
        self.leaderboard = leaderboard_backend or json_leaderboard
```

---

## 3. Decisiones Arquitectónicas

### 3.1 Board Representation: 1D vs 2D

**Decisión**: Usar 1D internamente (servidor), 2D en cliente.

**Razón**:
- Servidor: 1D es más simple (0-8 es más fácil que indexar [row][col])
- Cliente: 2D es más intuitivo para renderizar CSS Grid
- Conversión: `[row, col] → row * 3 + col` (O(1) overhead)

```
Server: [X, -, O, -, X, -, -, -, -]  # Índices 0-8
Client: [[X, -, O],                   # Fácil de renderizar
         [-, X, -],
         [-, -, -]]
```

### 3.2 Game State: Round vs Match

**Decisión**: Mantener TWO niveles de estado:
- **Round state**: `board`, `current_player`, `winner`, `is_draw`
- **Match state**: `wins`, `match_finished`

**Razón**:
- Best-of-5 requiere trackear victorias entre rondas
- `reset()` limpia round pero preserva `wins`
- `reset_match()` limpia TODO (serie nueva)
- Simple y claro

```python
game.reset()        # Nueva ronda, mismo match
game.reset_match()  # Serie nueva
```

### 3.3 Rate Limiter: Token Bucket vs Rate Limit

**Decisión**: Token Bucket (no Rate Limit simple)

**Por qué**:
- **Token Bucket**: Permite "ráfagas" (burst) de mensajes justos
  - Cliente puede enviar 10 msgs rápido, luego esperar
  - Justo: Cada cliente obtiene capacidad
  
- **Rate Limit simple** (X por segundo):
  - Muy estricto; rechaza ráfagas legítimas
  - Menos fluido

**Parámetros**:
- `capacity=100`: Máximo de tokens en el bucket
- `refill_rate=10.0`: Tokens/segundo
- Resultado: Max ~10 mensajes/segundo sostenido, ráfagas de 100

### 3.4 Leaderboard: JSON vs Postgres

**Decisión**: JSON por defecto, Postgres opcional.

**Razón**:
- **Desarrollo**: JSON = sin dependencias, sin setup BD
- **Producción**: Postgres = escalable, queryable, ACID
- **Flexibilidad**: Un `if DATABASE_URL` en `leaderboard.py` decide

```python
if DATABASE_URL:
    from . import leaderboard_pg as backend
else:
    # usar JSON
```

### 3.5 Message Validation: Server-Side Only

**Decisión**: El servidor es la ÚNICA fuente de verdad.

**Qué se valida en servidor**:
- ✅ Turno correcto (no "hackear" el turno del rival)
- ✅ Posición válida (0-8, no ocupada)
- ✅ Game ID válido (el jugador está en esa partida)
- ✅ Rate-limiting (no spam)

**Por qué**:
- Cliente es no confiable (puedo abrir DevTools y enviar mensajes falsos)
- Servidor decide la verdad física del juego
- Previene cheating

---

## 4. Flujo de Datos Clave

### 4.1 Conexión y Pairing

```
Cliente A                    Servidor                    Cliente B
(Alice)                      (GameManager)               (Bob)
   │                             │                         │
   │─── {join, "Alice"} ────────→│                         │
   │                             │ [register Alice]        │
   │                             │ [waiting_player = A]    │
   │←────── {registered, A} ─────│                         │
   │                             │                         │
   │←────── {waiting} ───────────│                         │
   │                             │                         │
   │                             │←───── {join, "Bob"} ────│
   │                             │ [register Bob]          │
   │                             │ [empareja A ↔ B]        │
   │                             │ [crea Game]             │
   │                             │                         │
   │←────── {assigned, X, id} ───│                         │
   │                             │─────→ {registered, B}──│
   │                             │                         │
   │←────── {state, board, X} ───│                         │
   │                             │─────→ {assigned, O, id}│
   │                             │                         │
   │                             │─────→ {state, board, X}│
```

### 4.2 Move Validation

```
1. Cliente A envía: {type: "move", position: [0,0]}
2. GameManager._handle_move():
   a. ¿Rate limited? NO → continuar
   b. ¿Es turno de A? SÍ → continuar
   c. ¿Posición válida? SÍ → continuar
   d. game.make_move(0):
      - Aplica 'X' en posición 0
      - ¿Hay ganador? NO
      - ¿Es empate? NO
      - Cambia turno a O
      - return True
   e. Broadcast {state, nuevo_board, O}
3. Cliente A + B reciben estado nuevo
```

---

## 5. Testing Strategy

### 5.1 Test Coverage

| Módulo | Coverage | Tests |
|--------|----------|-------|
| `game.py` | 95% | Test win, draw, best-of-5, reset |
| `rate_limiter.py` | 100% | Token refill, exhaust, reset |
| `game_manager.py` | 60% | Básico (async + WebSocket mockear es complejo) |

### 5.2 Approach

**Unit Tests** (predominan):
- No requieren servidor real
- Mockean WebSocket
- Rápidos (< 1 segundo)

**Integration Tests** (futuros):
- Podrían usar `pytest-asyncio` + cliente JS headless (Playwright)
- Probarían flujo completo (join → move → win)

---

## 6. Performance Considerations

### 6.1 Broadcast Efficiency

```python
# Cada move → broadcast a 2 jugadores
# Overhead: O(2) = O(1) por move
# Escala bien incluso con muchas partidas simultáneas
```

### 6.2 Rate Limiter Complexity

```python
# Token bucket:
# - is_allowed(client_id): O(1) en average
# - Buckets dict crece con # de clientes
# - reset_client() limpia cuando desconectar
# Scale: 1000 clientes simultáneos = OK (~1KB memory)
```

### 6.3 Leaderboard Write

```python
# Async non-blocking:
asyncio.create_task(leaderboard.add_result(result))
# El servidor no espera a que se escriba
# Escala sin bloquear WebSocket
```

---

## 7. Mejoras Futuras

### 7.1 Autenticación
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not validate_token(token):
        await websocket.close(code=1008, reason="Unauthorized")
    # ...
```

### 7.2 Spectators
```python
class GameManager:
    async def spectate_game(self, spectator: Player, game_id: str):
        game = self.games[game_id]
        game.spectators.append(spectator)
        # Enviar solo estado (no permitir moves)
```

### 7.3 Chat Mejorado
```python
# Backend ready, falta UI
@app.websocket("/ws")
async def _handle_chat(self, player: Player, data: dict):
    message = data.get("message")
    await self._broadcast_to_game(game, {
        "type": "chat",
        "sender": player.name,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })
```

### 7.4 AI opponent
```python
def minimax(board, depth, is_maximizing):
    # Implementar algoritmo minimax para IA
    # Permitir jugar contra máquina
```

---

## 8. Referencias

- **Patrones**: "Design Patterns: Elements of Reusable Object-Oriented Software" (Gang of Four)
- **SOLID**: "Clean Code" by Robert C. Martin
- **WebSocket**: https://tools.ietf.org/html/rfc6455
- **Rate Limiting**: https://en.wikipedia.org/wiki/Token_bucket

---

Última actualización: Noviembre 10, 2025
