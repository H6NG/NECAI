import sys
sys.path.append("../model")

import torch
import chess
from train import NECAIEvaluator, board_to_tensor_and_scalars

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

model = NECAIEvaluator().to(device)

checkpoint = torch.load("../model/necai_eval.pt", map_location=device)

# supports both old-style and new-style checkpoints
if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    model.load_state_dict(checkpoint["model_state_dict"])
else:
    model.load_state_dict(checkpoint)

model.eval()


def evaluate(fen):
    board_x, scalar_x = board_to_tensor_and_scalars(fen)
    board_x = board_x.unsqueeze(0).to(device)
    scalar_x = scalar_x.unsqueeze(0).to(device)

    with torch.no_grad():
        score = model(board_x, scalar_x).item()

    return round(score, 4)


print("Starting position:        ", evaluate("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
print("After 1. e4:              ", evaluate("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"))
print("White up a queen:         ", evaluate("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
print("Black up a queen:         ", evaluate("rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNB1KBNR w KQkq - 0 1"))
print("White up a rook:          ", evaluate("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"))
print("Scholar's mate:           ", evaluate("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4"))

board = chess.Board()
scores = []

for move in board.legal_moves:
    board.push(move)
    score = evaluate(board.fen())
    scores.append((move.uci(), score))
    board.pop()

scores.sort(key=lambda x: x[1], reverse=True)

print("\nTop 5 moves from starting position:")
for uci, score in scores[:5]:
    print(f"  {uci}  →  {score}")

print("\nBottom 5 moves from starting position:")
for uci, score in scores[-5:]:
    print(f"  {uci}  →  {score}")