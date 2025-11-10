from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models.game_manager import GameManager
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Para desarrollo: permitir orígenes. En producción restringir a orígenes confiables.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = GameManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Log para depuración: cabeceras y origen
    logging.info("Attempting websocket connection")
    try:
        headers = dict(websocket.headers)
        logging.info(f"Headers: {headers}")
        logging.info(f"Origin header: {websocket.headers.get('origin')}")
    except Exception:
        # Fallback si headers no se pueden leer directamente
        try:
            headers = {k.decode(): v.decode() for k, v in websocket.scope.get("headers", [])}
            logging.info(f"Headers fallback: {headers}")
        except Exception:
            logging.info("No se pudieron leer cabeceras de websocket")

    try:
        await websocket.accept()
        logging.info("Accepted websocket connection from client")
    except Exception as e:
        logging.exception("Accept failed")
        # Re-raise para que Uvicorn/Starlette maneje el cierre correctamente
        raise

    player = await manager.connect_player(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(player, data)
    except WebSocketDisconnect:
        await manager.disconnect_player(player)
# Nota: cualquier snippet de cliente (JavaScript) debe colocarse en archivos estáticos
# o en la consola del navegador. No incluir código JS en este archivo Python.