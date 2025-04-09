import chess  # Using python-chess library for move generation and validation
import random

# Initialize a chess board
board = chess.Board()

# Piece values for evaluation (in centipawns)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Simple evaluation function: material count + basic positional bonuses
def evaluate_board(board):
    if board.is_checkmate():
        if board.turn:  # White's turn
            return -9999  # Loss for white
        else:
            return 9999  # Win for white
    if board.is_stalemate() or board.is_insufficient_material():
        return 0  # Draw

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value
                # Bonus for central control (simplified)
                if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                    score += 10
            else:
                score -= value
                if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                    score -= 10
    return score

# Minimax with Alpha-Beta pruning
def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing_player:  # White's turn
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:  # Black's turn
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval

# Find the best move
def find_best_move(board, depth=3):
    best_move = None
    best_value = float('-inf') if board.turn else float('inf')
    alpha = float('-inf')
    beta = float('inf')

    for move in board.legal_moves:
        board.push(move)
        value = minimax(board, depth - 1, alpha, beta, not board.turn)
        board.pop()

        if board.turn:  # White maximizes
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
        else:  # Black minimizes
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, value)

    return best_move

# Simple game loop
def play_game():
    print("Starting Chess Game!")
    print(board)
    while not board.is_game_over():
        if board.turn:  # Human plays as White
            move = input("Enter your move (e.g., 'e2e4'): ")
            try:
                board.push_san(move)
            except ValueError:
                print("Invalid move! Try again.")
                continue
        else:  # AI plays as Black
            print("AI thinking...")
            ai_move = find_best_move(board, depth=3)
            print(f"AI move: {ai_move}")
            board.push(ai_move)
        print(board)
        print("---------------")

    result = board.result()
    print(f"Game Over! Result: {result}")

# Run the game
if __name__ == "__main__":
    # Requires 'python-chess' library: pip install chess
    play_game()