# Quick Start Guide 🚀

## 30 segundos para jugar

### 1. Instalar & Ejecutar

```bash
# Windows
run.bat

# macOS/Linux
chmod +x run.sh
./run.sh
```

### 2. Abrir en navegador

```
http://localhost:8080  (Cliente)
http://localhost:8000  (Servidor)
```

### 3. ¡A jugar!

- **Multijugador**: 2 navegadores, haz clic en "Conectar"
- **Single-Player**: Haz clic en "Single-Player (IA)", elige dificultad

---

## Manual Completo

### Instalación Manual

```bash
# 1. Backend
cd server
pip install -r requirements.txt

# 2. Tests (opcional)
pytest tests/ -v

# 3. Servidor
python -m uvicorn main:app --reload
```

### Frontend (otro terminal)

```bash
cd client
python -m http.server 8080
# o si tienes Python 2:
# python -m SimpleHTTPServer 8080
```

### URLs

| Componente | URL |
|-----------|-----|
| Cliente Web | http://localhost:8080 |
| API WebSocket | ws://localhost:8000/ws |
| Leaderboard REST | http://localhost:8000/leaderboard |
| Single-Player API | http://localhost:8000/api/single-player/* |

---

## Modos de Juego

### 🎮 Multijugador (WebSocket)

```javascript
// Flow automático:
1. Jugador A abre tab → "Conectar"
2. Jugador B abre tab → "Conectar"
3. Se emparejan automáticamente
4. Juegan best-of-5 (primero a 3 victorias)
5. Pueden reiniciar serie con botón
6. Resultado guardado en leaderboard
```

### 🤖 Single-Player (REST API)

```javascript
// Flow automático:
1. Selecciona dificultad (Fácil/Media/Difícil)
2. Haz clic en "Iniciar Juego vs IA"
3. Eres X (comienzas primero)
4. IA responde con Minimax (casi imposible ganar)
5. Juega best-of-5
6. Puedes reiniciar serie
```

---

## Dificultades Disponibles

| Nivel | Descripción | Dificultad |
|-------|-----------|-----------|
| **Fácil** | Movimientos al azar | ⭐ Muy fácil |
| **Media** | 70% Minimax, 30% random | ⭐⭐⭐ Difícil |
| **Difícil** | 100% Minimax puro | ⭐⭐⭐⭐⭐ Imposible |

---

## Controles

### Mouse/Trackpad
- Haz clic en una celda vacía para jugar
- Botones en la interfaz para conectar/reiniciar

### Teclado
- **Enter** en chat: enviar mensaje
- **Ctrl+C** en terminal: detener servidor

---

## Troubleshooting

### "No puedo conectar al servidor"

```bash
# Verifica que el servidor está corriendo:
# Terminal 1: cd server && python -m uvicorn main:app --reload
# Terminal 2: cd client && python -m http.server 8080

# Si el puerto está ocupado:
python -m uvicorn main:app --port 9000
# Luego edita client/js/ws.js línea de conexión
```

### "Tests no funcionan"

```bash
cd server
pip install pytest pytest-asyncio
pytest tests/ -v
```

### "Error de CORS"

Ya está configurado. Si cambian orígenes, editar:
```python
# server/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← Cambiar aquí en producción
)
```

### "La IA es muy lenta"

Normal en primer turno (~500ms). Posterior son ~50-100ms.

---

## Estructura de Carpetas

```
proyecto1/
├── client/                 # Frontend
│   ├── index.html         # Página principal
│   ├── css/styles.css     # Estilos
│   └── js/
│       ├── main.js        # Lógica principal
│       ├── sp.js          # Single-player manager
│       ├── ws.js          # WebSocket client
│       └── ui.js          # Renderizado
│
├── server/                # Backend
│   ├── main.py           # FastAPI app
│   ├── models/           # Lógica de juego
│   │   ├── game.py
│   │   ├── game_manager.py
│   │   ├── player.py
│   │   └── factory.py
│   ├── ai/               # IA Minimax
│   │   └── minimax.py
│   ├── utils/            # Utilidades
│   │   ├── rate_limiter.py
│   │   ├── error_codes.py
│   │   └── message_types.py
│   ├── tests/            # Tests pytest
│   │   ├── test_game.py
│   │   ├── test_rate_limiter.py
│   │   └── test_minimax.py
│   ├── leaderboard.py    # JSON/PostgreSQL
│   └── requirements.txt
│
├── README.md            # Documentación principal
├── ARCHITECTURE.md      # Design patterns y arquitectura
├── SINGLE_PLAYER.md     # Guía de IA
├── TESTING.md           # Testing guide
├── COMPLETION_REPORT.md # Resumen de implementación
├── run.sh               # Script ejecutable (Linux/Mac)
└── run.bat              # Script ejecutable (Windows)
```

---

## Database Setup (Opcional)

### Con PostgreSQL

```bash
# Instalar PostgreSQL
# Crear database:
createdb triqui

# Exportar URL en .env:
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/triqui"

# O en Windows:
set DATABASE_URL=postgresql+asyncpg://user:pass@localhost/triqui

# Luego ejecutar servidor
python -m uvicorn main:app --reload
```

### Sin PostgreSQL (Default)

```bash
# Usa JSON local automáticamente
python -m uvicorn main:app --reload
```

---

## Endpoints REST

### Leaderboard

```bash
# Get
curl http://localhost:8000/leaderboard

# Post
curl -X POST http://localhost:8000/leaderboard \
  -H "Content-Type: application/json" \
  -d '{"winner_name":"Juan","loser_name":"María"}'

# Clear
curl -X DELETE http://localhost:8000/leaderboard
```

### Single-Player

```bash
# Crear juego
curl -X POST http://localhost:8000/api/single-player/game

# Hacer movimiento
curl -X POST http://localhost:8000/api/single-player/{game_id}/move \
  -d '{"position":[0,0]}'

# Reset ronda
curl -X POST http://localhost:8000/api/single-player/{game_id}/reset

# Reset match
curl -X POST http://localhost:8000/api/single-player/{game_id}/reset-match
```

---

## Documentación Completa

- **README.md** - Overview y setup
- **ARCHITECTURE.md** - Design patterns, SOLID, complejidad
- **SINGLE_PLAYER.md** - Guía de IA Minimax
- **TESTING.md** - Cómo ejecutar tests
- **COMPLETION_REPORT.md** - Resumen total del proyecto

---

## Atajos Útiles

```bash
# Terminal 1: Servidor
cd server && python -m uvicorn main:app --reload

# Terminal 2: Cliente
cd client && python -m http.server 8080

# Terminal 3: Tests (mientras servidor corre)
cd server && pytest tests/ -v

# Tests con cobertura
pytest tests/ --cov=models --cov=utils --cov=ai --cov-report=html
```

---

## Tips para Jugar

### Multijugador
- X va primero (ventaja)
- 30 segundos por turno (timeout automático)
- Gana 3 rondas para ganar el match
- Puedes chatear durante la partida

### Single-Player
- Eres X (ventaja)
- IA es prácticamente imbatible en dificultad alta
- Dificultad media es más balanceada
- Dificultad fácil es puro luck

---

## Performance

| Métrica | Valor |
|---------|-------|
| Tiempo a 1er movimiento | < 100ms |
| Tiempo a respuesta IA | 50-500ms |
| Latencia WebSocket | ~20-50ms |
| Test coverage | ~90% |
| Líneas de código | ~4500 |

---

## Próximos Pasos

1. ✅ Juega multijugador
2. ✅ Prueba contra la IA
3. 📖 Lee ARCHITECTURE.md para entender el diseño
4. 🧪 Ejecuta tests: `pytest tests/`
5. 📝 Modifica y personaliza

---

## Licencia & Autor

Proyecto académico - Semestre 11 - Arquitectura Cliente-Servidor

**Última actualización**: 2024
