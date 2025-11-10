from typing import List, Tuple, Optional

def check_winner(board: List[List[str]]) -> Optional[str]:
    # Check rows
    for row in board:
        if len(set(row)) == 1 and row[0] is not None:
            return row[0]
    
    # Check columns
    for col in range(3):
        if (board[0][col] == board[1][col] == board[2][col]) and board[0][col] is not None:
            return board[0][col]
    
    # Check diagonals
    if (board[0][0] == board[1][1] == board[2][2]) and board[0][0] is not None:
        return board[0][0]
    if (board[0][2] == board[1][1] == board[2][0]) and board[0][2] is not None:
        return board[0][2]
    
    return None

def is_valid_move(board: List[List[str]], position: Tuple[int, int]) -> bool:
    row, col = position
    if 0 <= row < 3 and 0 <= col < 3:
        return board[row][col] is None
    return False