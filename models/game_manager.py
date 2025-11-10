from typing import Dict, Optional
import logging
import asyncio
from uuid import uuid4

from models.game import Game
from models.player import PlayerConnection
import utils.message_types as mt

logger = logging.getLogger(__name__)

class GameManager:
    """Gestiona las conexiones de jugadores y las partidas."""
    
    def __init__(self):
        """Inicializa el gestor de juegos."""
        self._players: Dict[str, PlayerConnection] = {}  # player_id -> PlayerConnection
        self.games: Dict[str, Game] = {}  # game_id -> Game
        self._waiting_player: Optional[str] = None  # ID del jugador en espera
        self._cleanup_tasks = {}  # Tareas de limpieza por jugador
        
    async def register_player(self, websocket, name: str) -> PlayerConnection:
        """Registra un nuevo jugador."""
        player_id = str(uuid4())
        player = PlayerConnection(player_id, name, websocket)
        self._players[player_id] = player
        logger.info(f"Jugador registrado: {name} ({player_id})")
        return player

    async def connect_and_pair(self, player: PlayerConnection) -> Optional[Game]:
        """Conecta un jugador y lo empareja si hay otro esperando."""
        if player.game_id:
            # Si el jugador ya está en una partida, reconectarlo
            game = self.games.get(player.game_id)
            if game:
                player.connected = True
                await self._broadcast_game_state(game)
                logger.info(f"Jugador {player.name} reconectado a la partida {game.id}")
                return game
            else:
                player.game_id = None

        # Si no hay jugador esperando, este jugador espera
        if not self._waiting_player:
            self._waiting_player = player.id
            player.connected = True
            await player.send({
                "type": mt.MessageType.WAITING.value,
                "message": "Esperando a otro jugador..."
            })
            return None

        # Si el jugador que espera es el mismo, actualizar su conexión
        if self._waiting_player == player.id:
            player.connected = True
            await player.send({
                "type": mt.MessageType.WAITING.value,
                "message": "Esperando a otro jugador..."
            })
            return None

        # Emparejar con el jugador que espera
        waiting_player = self._players.get(self._waiting_player)
        if not waiting_player or not waiting_player.connected:
            # Si el jugador que espera ya no está disponible, este jugador pasa a esperar
            self._waiting_player = player.id
            player.connected = True
            await player.send({
                "type": mt.MessageType.WAITING.value,
                "message": "Esperando a otro jugador..."
            })
            return None

        # Crear nueva partida
        game = Game()
        game.player_x = waiting_player.id
        game.player_o = player.id
        self.games[game.id] = game

        # Actualizar estado de los jugadores
        waiting_player.game_id = game.id
        player.game_id = game.id
        player.connected = True

        # Limpiar jugador en espera
        self._waiting_player = None

        # Notificar a ambos jugadores
        await self._broadcast_game_state(game)
        logger.info(f"Nueva partida {game.id}: {waiting_player.name} vs {player.name}")
        return game

    async def handle_message(self, player: PlayerConnection, data: dict):
        """Procesa mensajes del jugador."""
        try:
            mtype = mt.MessageType(data.get("type"))
        except ValueError:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": f"Tipo de mensaje inválido: {data.get('type')}"
            })
            return

        handlers = {
            mt.MessageType.MOVE: self._handle_move,
            mt.MessageType.GAME_RESET: self._handle_reset,
            mt.MessageType.CHAT_MESSAGE: self._handle_chat
        }

        handler = handlers.get(mtype)
        if handler:
            await handler(player, data)
        else:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": f"Tipo de mensaje no soportado: {mtype}"
            })

    async def _handle_move(self, player: PlayerConnection, data: dict):
        """Procesa un movimiento del jugador."""
        if not player.game_id:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "No estás en una partida"
            })
            return

        game = self.games.get(player.game_id)
        if not game:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "Partida no encontrada"
            })
            return

        if game.current_player != player:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "No es tu turno"
            })
            return

        try:
            pos = data.get("position")
            if not isinstance(pos, int) or pos < 0 or pos > 8:
                raise ValueError("Posición debe ser un número entre 0 y 8")
            
            if not game.make_move(pos):
                await player.send({
                    "type": mt.MessageType.ERROR.value,
                    "message": "Casilla ya ocupada o movimiento inválido"
                })
                return

            # Actualizar estado del juego
            await self._broadcast_game_state(game)
            
            # Verificar fin del juego
            if game.winner:
                winner = self._players.get(game.winner)
                await self._broadcast_to_game(game, {
                    "type": mt.MessageType.GAME_OVER.value,
                    "winner": winner.name if winner else "Desconocido",
                    "board": game.board
                })
            elif game.is_draw:
                await self._broadcast_to_game(game, {
                    "type": mt.MessageType.GAME_OVER.value,
                    "winner": "Empate",
                    "board": game.board
                })

        except (ValueError, TypeError) as e:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": f"Error en el movimiento: {str(e)}"
            })

    async def _handle_reset(self, player: PlayerConnection, data: dict):
        """Reinicia una partida - ambos jugadores deben estar de acuerdo."""
        if not player.game_id:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "No estás en una partida"
            })
            return

        game = self.games.get(player.game_id)
        if not game:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "Partida no encontrada"
            })
            return

        # Reiniciar el juego
        game.reset()
        
        # Notificar a los jugadores
        await self._broadcast_to_game(game, {
            "type": mt.MessageType.GAME_RESET.value,
            "board": game.board,
            "current_player": "X" if game.current_player == game.player_x else "O"
        })

    async def _handle_chat(self, player: PlayerConnection, data: dict):
        """Maneja mensajes de chat entre jugadores."""
        if not player.game_id:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "No estás en una partida"
            })
            return

        game = self.games.get(player.game_id)
        if not game:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "Partida no encontrada"
            })
            return

        message = data.get("message", "").strip()
        if not message:
            await player.send({
                "type": mt.MessageType.ERROR.value,
                "message": "Mensaje vacío"
            })
            return

        # Enviar mensaje a todos los jugadores en la partida
        await self._broadcast_to_game(game, {
            "type": mt.MessageType.CHAT_MESSAGE.value,
            "sender": player.name,
            "message": message
        })

    async def _broadcast_game_state(self, game: Game):
        """Envía el estado actual del juego a todos los jugadores."""
        await self._broadcast_to_game(game, {
            "type": mt.MessageType.GAME_STATE.value,
            "board": game.board,
            "current_player": "X" if game.current_player == game.player_x else "O",
            "player_x": self._get_player_info(game.player_x),
            "player_o": self._get_player_info(game.player_o)
        })

    async def _broadcast_to_game(self, game: Game, message: dict):
        """Envía un mensaje a todos los jugadores en una partida."""
        players = []
        if game.player_x:
            players.append(self._players.get(game.player_x))
        if game.player_o:
            players.append(self._players.get(game.player_o))

        for player in players:
            if player and player.websocket:
                try:
                    await player.send(message)
                except Exception as e:
                    logger.error(f"Error al enviar mensaje a {player.name}: {str(e)}")
                    player.connected = False
                    asyncio.create_task(self._handle_disconnect(player))

    def _get_player_info(self, player_id: str) -> dict:
        """Obtiene información básica de un jugador."""
        player = self._players.get(player_id)
        if not player:
            return {"id": player_id, "name": "Desconocido", "connected": False}
        return {
            "id": player.id,
            "name": player.name,
            "connected": player.connected
        }

    async def _handle_disconnect(self, player: PlayerConnection):
        """Maneja la desconexión de un jugador."""
        if not player:
            return

        player.connected = False
        logger.info(f"Jugador {player.name} desconectado")

        # Notificar a otros jugadores en la partida
        if player.game_id:
            game = self.games.get(player.game_id)
            if game:
                await self._broadcast_game_state(game)

        # Si el jugador estaba esperando, limpiar el estado de espera
        if self._waiting_player == player.id:
            self._waiting_player = None

        # Iniciar temporizador para limpiar el jugador si no se reconecta
        asyncio.create_task(self._schedule_player_cleanup(player))

    async def _schedule_player_cleanup(self, player: PlayerConnection):
        """Programa la limpieza de un jugador después de un tiempo si no se reconecta."""
        await asyncio.sleep(300)  # 5 minutos

        # Si el jugador sigue desconectado, limpiar
        if player.id in self._players and not player.connected:
            # Limpiar la partida si existe
            if player.game_id and player.game_id in self.games:
                game = self.games[player.game_id]
                # Notificar al otro jugador antes de limpiar
                other_player_id = game.player_o if game.player_x == player.id else game.player_x
                if other_player_id:
                    other_player = self._players.get(other_player_id)
                    if other_player and other_player.connected:
                        await other_player.send({
                            "type": mt.MessageType.GAME_ABANDONED.value,
                            "message": f"El jugador {player.name} ha abandonado la partida"
                        })
                # Eliminar la partida
                del self.games[player.game_id]

            # Eliminar el jugador
            del self._players[player.id]
            logger.info(f"Jugador {player.name} eliminado por inactividad")