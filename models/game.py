from typing import List, Optional, Dict, Tuple
from .player import PlayerConnection as Player

class Game:
    def __init__(self, game_id: str, player_x: Player, player_o: Player):
        self.game_id = game_id
        self.player_x = player_x
        self.player_o = player_o
        self.board = [["-" for _ in range(3)] for _ in range(3)]
        self.turn = "X"
        self.wins = {"X": 0, "O": 0}
        self.finished = False
        self.winner = None
        self.moves_count = 0

    def get_player_symbol(self, player: Player) -> Optional[str]:
        """Retorna el símbolo (X/O) del jugador"""
        if player == self.player_x:
            return "X"
        elif player == self.player_o:
            return "O"
        return None

    def is_valid_move(self, row: int, col: int) -> bool:
        """Verifica si el movimiento es válido"""
        return (
            0 <= row < 3 
            and 0 <= col < 3 
            and self.board[row][col] == "-"
            and not self.finished
        )

    def check_winner(self) -> Optional[str]:
        """Verifica si hay un ganador y retorna su símbolo"""
        # Revisar filas
        for row in self.board:
            if row[0] != "-" and row[0] == row[1] == row[2]:
                return row[0]

        # Revisar columnas
        for col in range(3):
            if (self.board[0][col] != "-" 
                and self.board[0][col] == self.board[1][col] == self.board[2][col]):
                return self.board[0][col]

        # Revisar diagonales
        if (self.board[0][0] != "-" 
            and self.board[0][0] == self.board[1][1] == self.board[2][2]):
            return self.board[0][0]
        
        if (self.board[0][2] != "-" 
            and self.board[0][2] == self.board[1][1] == self.board[2][0]):
            return self.board[0][2]

        return None

    async def make_move(self, player: Player, row: int, col: int) -> Dict:
        """Realiza un movimiento y retorna el resultado"""
        # Validar el movimiento
        player_symbol = self.get_player_symbol(player)
        if not player_symbol:
            return {"error": "No eres parte de este juego"}
        
        if player_symbol != self.turn:
            return {"error": "No es tu turno"}
        
        if not self.is_valid_move(row, col):
            return {"error": "Movimiento inválido"}

        # Realizar el movimiento
        self.board[row][col] = player_symbol
        self.moves_count += 1

        # Verificar si hay ganador
        winner = self.check_winner()
        is_draw = self.moves_count == 9

        # Actualizar estado del juego
        if winner:
            self.winner = winner
            self.wins[winner] += 1
            self.finished = True
        elif is_draw:
            self.finished = True

        # Cambiar turno
        self.turn = "O" if self.turn == "X" else "X"

        # Preparar respuesta
        return {
            "type": "move",
            "success": True,
            "board": self.board,
            "turn": self.turn,
            "finished": self.finished,
            "winner": self.winner,
            "is_draw": is_draw and not winner,
            "wins": self.wins
        }

    def reset_board(self):
        """Reinicia el tablero para una nueva partida"""
        self.board = [["-" for _ in range(3)] for _ in range(3)]
        self.turn = "X"
        self.finished = False
        self.winner = None
        self.moves_count = 0

    def get_game_state(self) -> Dict:
        """Retorna el estado actual del juego"""
        return {
            "game_id": self.game_id,
            "board": self.board,
            "turn": self.turn,
            "finished": self.finished,
            "winner": self.winner,
            "wins": self.wins,
            "player_x": self.player_x.name,
            "player_o": self.player_o.name
        }