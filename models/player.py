import uuid
from typing import Optional


class PlayerConnection:
    def __init__(self, websocket, name: Optional[str] = None):
        self.websocket = websocket
        self.id = str(uuid.uuid4())
        self.name = name or f"Player-{self.id[:8]}"
        self.symbol: Optional[str] = None
        self.game_id: Optional[str] = None
        self.connected: bool = True

    async def send(self, message: dict):
        """Enviar JSON al websocket del jugador (si está conectado)."""
        if self.connected and self.websocket:
            await self.websocket.send_json(message)

    async def close(self):
        try:
            await self.websocket.close()
        except Exception:
            pass

    def __eq__(self, other):
        if not isinstance(other, PlayerConnection):
            return False
        return self.id == other.id
