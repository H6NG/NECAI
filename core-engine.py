import chess
import pygame
import time

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 512, 512
SQUARE_SIZE = WIDTH // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neural Engine Chess AI")

# Load piece images (assumes you have 64x64 PNGs named like 'wP.png', 'bK.png' in a 'pieces' folder)
PIECE_IMAGES = {}
for color in ['w', 'b']:
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        PIECE_IMAGES[color + piece] = pygame.transform.scale(
            pygame.image.load(f"pieces/{color}{piece}.svg"), (SQUARE_SIZE, SQUARE_SIZE)
        )

# Chess board and piece mapping
board = chess.Board()
PIECE_MAP = {
    chess.PAWN: 'P', chess.KNIGHT: 'N', chess.BISHOP: 'B',
    chess.ROOK: 'R', chess.QUEEN: 'Q', chess.KING: 'K'
}
COLOR_MAP = {chess.WHITE: 'w', chess.BLACK: 'b'}

# Piece values and evaluation
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = PIECE_VALUES[piece.piece_type]
            score += value if piece.color == chess.WHITE else -value
            if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                score += 10 if piece.color == chess.WHITE else -10
    return score

# Minimax with Alpha-Beta pruning
def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
    if maximizing_player:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def find_best_move(board, depth=3):
    best_move = None
    best_value = float('-inf') if board.turn else float('inf')
    alpha = float('-inf')
    beta = float('inf')
    for move in board.legal_moves:
        board.push(move)
        value = minimax(board, depth - 1, alpha, beta, not board.turn)
        board.pop()
        if board.turn:
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
        else:
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, value)
    return best_move

# Draw the board and pieces
def draw_board(screen, board, selected_square=None):
    colors = [(245, 222, 179), (139, 69, 19)]  # Light and dark squares (wheat and brown)
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                piece_key = COLOR_MAP[piece.color] + PIECE_MAP[piece.piece_type]
                screen.blit(PIECE_IMAGES[piece_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))
    if selected_square is not None:
        col, row = chess.square_file(selected_square), 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, (255, 255, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

# Main game loop
def play_game():
    clock = pygame.time.Clock()
    selected_square = None
    running = True

    while running and not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and board.turn:  # White's turn (human)
                x, y = event.pos
                col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
                square = chess.square(col, 7 - row)
                if selected_square is None:
                    if board.piece_at(square) and board.piece_at(square).color == chess.WHITE:
                        selected_square = square
                else:
                    move = chess.Move(selected_square, square)
                    if move in board.legal_moves:
                        board.push(move)
                        selected_square = None
                    elif board.piece_at(square) and board.piece_at(square).color == chess.WHITE:
                        selected_square = square
                    else:
                        selected_square = None

        # Draw the board
        draw_board(screen, board, selected_square)
        pygame.display.flip()

        # AI move (Black)
        if not board.turn and not board.is_game_over():
            print("AI thinking...")
            ai_move = find_best_move(board, depth=3)
            board.push(ai_move)
            draw_board(screen, board)
            pygame.display.flip()
            time.sleep(0.5)  # Brief pause to see AI move

        clock.tick(60)

    # Game over
    draw_board(screen, board)
    pygame.display.flip()
    print(f"Game Over! Result: {board.result()}")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(60)

if __name__ == "__main__":
    play_game()
    pygame.quit()