from enum import Enum
from typing import Dict, Any

class MessageType(Enum):
    # Mensajes de conexión y sesión
    CONNECT = "connect"                    # Cliente se conecta al servidor
    DISCONNECT = "disconnect"              # Cliente se desconecta
    RECONNECT = "reconnect"               # Cliente intenta reconectarse
    
    # Mensajes de estado del juego
    WAITING = "waiting"                    # Esperando a otro jugador
    GAME_START = "game_start"             # Juego comienza
    GAME_STATE = "game_state"             # Actualización del estado del juego
    GAME_OVER = "game_over"               # Juego terminado
    GAME_RESET = "game_reset"             # Reiniciar el juego
    
    # Mensajes de jugador
    PLAYER_JOINED = "player_joined"       # Nuevo jugador se une
    PLAYER_LEFT = "player_left"           # Jugador abandona el juego
    PLAYER_DISCONNECTED = "player_disconnected"  # Jugador se desconecta
    PLAYER_RECONNECTED = "player_reconnected"    # Jugador se reconecta
    
    # Mensajes de juego
    MOVE = "move"                         # Realizar un movimiento
    INVALID_MOVE = "invalid_move"         # Movimiento inválido
    TURN_CHANGE = "turn_change"           # Cambio de turno
    
    # Mensajes de chat
    CHAT_MESSAGE = "chat_message"         # Mensaje de chat
    
    # Mensajes de error
    ERROR = "error"                       # Error general
    
    # Mensajes de sistema
    PING = "ping"                         # Verificar conexión
    PONG = "pong"                         # Respuesta a ping

class MessageBuilder:
    """
    Clase auxiliar para construir mensajes con el formato correcto
    """
    @staticmethod
    def create_message(message_type: MessageType, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea un mensaje con el formato estándar
        """
        message = {
            "type": message_type.value,
            "timestamp": None  # Se puede agregar timestamp si se necesita
        }
        
        if data:
            message.update(data)
            
        return message

    @staticmethod
    def error(message: str) -> Dict[str, Any]:
        """
        Crea un mensaje de error
        """
        return MessageBuilder.create_message(MessageType.ERROR, {
            "message": message
        })

    @staticmethod
    def game_state(board: list, turn: str, finished: bool = False, winner: str = None) -> Dict[str, Any]:
        """
        Crea un mensaje de estado del juego
        """
        return MessageBuilder.create_message(MessageType.GAME_STATE, {
            "board": board,
            "turn": turn,
            "finished": finished,
            "winner": winner
        })

    @staticmethod
    def move_result(success: bool, message: str = None, board: list = None) -> Dict[str, Any]:
        """
        Crea un mensaje de resultado de movimiento
        """
        return MessageBuilder.create_message(MessageType.MOVE, {
            "success": success,
            "message": message,
            "board": board
        })

    @staticmethod
    def chat(player_name: str, message: str) -> Dict[str, Any]:
        """
        Crea un mensaje de chat
        """
        return MessageBuilder.create_message(MessageType.CHAT_MESSAGE, {
            "player": player_name,
            "message": message
        })