import chess
import pygame
import time
import random

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 512, 512
SQUARE_SIZE = WIDTH // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neural Engine Chess AI")

# Colors
LIGHT_SQUARE = (245, 222, 179)  # Wheat
DARK_SQUARE = (139, 69, 19)     # Brown
HIGHLIGHT = (255, 255, 0)       # Yellow for selected square
TEXT_BG = (50, 50, 50)          # Dark background for prompt

# Load fonts
FONT = pygame.font.SysFont("arial", 24)

# Load piece images (assumes 64x64 images in 'pieces' folder, e.g., 'wP.png', 'bK.png')
PIECE_IMAGES = {}
for color in ['w', 'b']:
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        # Change '.svg' to '.png' if using PNGs
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

# Simple AI for testing (replace with your minimax if desired)
def find_best_move(board, depth=3):
    return random.choice(list(board.legal_moves))

# Draw the board and pieces
def draw_board(screen, board, selected_square=None):
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            piece = board.piece_at(chess.square(col, 7 - row))
            if piece:
                piece_key = COLOR_MAP[piece.color] + PIECE_MAP[piece.piece_type]
                screen.blit(PIECE_IMAGES[piece_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))
    if selected_square is not None:
        col, row = chess.square_file(selected_square), 7 - chess.square_rank(selected_square)
        pygame.draw.rect(screen, HIGHLIGHT, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

# Display prompt and get input
def get_ai_color(screen):
    input_string = ""
    ai_color = None
    prompt = "NECAI play white or black?"
    error_message = ""
    while ai_color is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_string.lower() == "white":
                        ai_color = chess.WHITE
                    elif input_string.lower() == "black":
                        ai_color = chess.BLACK
                    else:
                        error_message = "Please enter 'white' or 'black'"
                        input_string = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_string = input_string[:-1]
                elif event.unicode.isprintable():
                    input_string += event.unicode

        # Draw prompt screen
        screen.fill(TEXT_BG)
        prompt_text = FONT.render(prompt, True, (255, 255, 255))
        input_text = FONT.render(input_string, True, (255, 255, 255))
        error_text = FONT.render(error_message, True, (255, 0, 0))
        
        screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(input_text, (WIDTH // 2 - input_text.get_width() // 2, HEIGHT // 2))
        screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2 + 50))
        
        pygame.display.flip()
    
    return ai_color

# Main game loop
def play_game():
    clock = pygame.time.Clock()
    selected_square = None
    running = True

    # Get AI color
    ai = get_ai_color(screen)  # Stores chess.WHITE or chess.BLACK
    human = chess.BLACK if ai == chess.WHITE else chess.WHITE

    while running and not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and board.turn == human:
                x, y = event.pos
                col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
                square = chess.square(col, 7 - row)
                if selected_square is None:
                    if board.piece_at(square) and board.piece_at(square).color == human:
                        selected_square = square
                else:
                    move = chess.Move(selected_square, square)
                    if move in board.legal_moves:
                        board.push(move)
                        selected_square = None
                    elif board.piece_at(square) and board.piece_at(square).color == human:
                        selected_square = square
                    else:
                        selected_square = None

        # Draw the board
        draw_board(screen, board, selected_square)
        pygame.display.flip()

        # AI move
        if not board.is_game_over() and board.turn == ai:
            print("AI thinking...")
            ai_move = find_best_move(board)
            board.push(ai_move)
            draw_board(screen, board)
            pygame.display.flip()
            time.sleep(0.5)

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