"""
Visualize the classical (C++) evaluator's behavior across many positions.
Compares its output against material count and (optionally) the neural eval.

Usage:
    make eval_stream
    python -m evaluator.classical_eval.visualize
"""
import chess
import random
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
from pathlib import Path
from tqdm import tqdm

from evaluator.neural_eval.inference import load_model, get_device
from evaluator.neural_eval.struct import board_to_tensor_and_scalars

import torch

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3.2, chess.BISHOP: 3.3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0,
}

NUM_POSITIONS = 100_000
CHUNK_SIZE = 5000
NUM_PROC = 8
SEED = 42

ROOT = Path(__file__).resolve().parents[2]
EVAL_BIN = ROOT / "eval_stream"
CP_SCALE = 600.0  # match training: tanh(cp/600)


def material_advantage(board):
    score = 0
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        score += val if piece.color == chess.WHITE else -val
    return score


def random_game_position():
    plies = random.randint(8, 60)
    board = chess.Board()
    for _ in range(plies):
        if board.is_game_over():
            break
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(random.choice(moves))
    return board


def remove_random_pieces(board, color, ptype, count):
    sqs = list(board.pieces(ptype, color))
    random.shuffle(sqs)
    removed = 0
    for sq in sqs:
        if removed >= count:
            break
        if board.piece_at(sq).piece_type != chess.KING:
            board.remove_piece_at(sq)
            removed += 1
    return removed == count and board.is_valid()


def make_imbalance():
    board = chess.Board()
    color = random.choice([chess.WHITE, chess.BLACK])
    for _ in range(random.randint(1, 3)):
        ptype = random.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
        n = random.randint(1, 2 if ptype == chess.PAWN else 1)
        remove_random_pieces(board, color, ptype, n)
    return board


def random_endgame():
    board = chess.Board.empty()
    sqs = list(range(64))
    random.shuffle(sqs)
    wk, bk = sqs[0], sqs[1]
    if abs((wk % 8) - (bk % 8)) <= 1 and abs((wk // 8) - (bk // 8)) <= 1:
        bk = sqs[2]
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    used = {wk, bk}
    for _ in range(random.randint(0, 6)):
        sq = random.choice([s for s in sqs if s not in used])
        used.add(sq)
        ptype = random.choice([chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
        color = random.choice([chess.WHITE, chess.BLACK])
        if ptype == chess.PAWN and (sq // 8 == 0 or sq // 8 == 7):
            continue
        board.set_piece_at(sq, chess.Piece(ptype, color))
    board.turn = random.choice([chess.WHITE, chess.BLACK])
    return board if board.is_valid() else None


def make_chunk(args):
    seed, n = args
    random.seed(seed)
    out = []
    while len(out) < n:
        r = random.random()
        if r < 0.6:
            board = random_game_position(); cat = "random"
        elif r < 0.78:
            board = make_imbalance(); cat = "imbalance"
        elif r < 0.9:
            board = random_endgame(); cat = "endgame"
        elif r < 0.97:
            board = chess.Board(); cat = "opening"
            for _ in range(random.randint(0, 8)):
                if board.is_game_over():
                    break
                board.push(random.choice(list(board.legal_moves)))
        else:
            board = random_game_position(); cat = "tactical"
        if board is None or not board.is_valid():
            continue
        out.append((cat, board.fen(), material_advantage(board)))
    return out


def run_classical_eval(fens):
    """Pipe FENs into the C++ binary, return scores in centipawns."""
    if not EVAL_BIN.exists():
        raise FileNotFoundError(
            f"{EVAL_BIN} not found. Build it with `make eval_stream` from {ROOT}"
        )
    proc = subprocess.Popen(
        [str(EVAL_BIN)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    input_str = "\n".join(fens) + "\n"
    out, _ = proc.communicate(input_str)
    return np.array([int(line) for line in out.strip().split("\n")], dtype=np.float32)


def fen_to_tensors(fen):
    return board_to_tensor_and_scalars(fen)


def run_neural_eval(fens, batch_size=4096):
    """Run the trained neural model on a list of FENs (returns tanh-scaled scores)."""
    model = load_model()
    device = get_device()
    model.eval()

    scores = np.empty(len(fens), dtype=np.float32)
    with Pool(NUM_PROC) as pool:
        for start in tqdm(range(0, len(fens), batch_size), desc="Neural"):
            end = min(start + batch_size, len(fens))
            tensors = pool.map(fen_to_tensors, fens[start:end])
            board_x = torch.stack([t[0] for t in tensors]).to(device)
            scalar_x = torch.stack([t[1] for t in tensors]).to(device)
            with torch.no_grad():
                preds = model(board_x, scalar_x).cpu().numpy().flatten()
            scores[start:end] = preds
    return scores


def main():
    print(f"Generating {NUM_POSITIONS:,} positions...")
    n_chunks = (NUM_POSITIONS + CHUNK_SIZE - 1) // CHUNK_SIZE
    chunk_args = [(SEED + i, min(CHUNK_SIZE, NUM_POSITIONS - i * CHUNK_SIZE))
                  for i in range(n_chunks)]

    cats_all, fens_all, materials_all = [], [], []
    with Pool(NUM_PROC) as pool:
        for chunk in tqdm(pool.imap_unordered(make_chunk, chunk_args),
                          total=n_chunks, desc="Generate"):
            for cat, fen, mat in chunk:
                cats_all.append(cat)
                fens_all.append(fen)
                materials_all.append(mat)

    n = len(fens_all)
    materials = np.array(materials_all, dtype=np.float32)
    cats = np.array(cats_all)

    print("Running classical eval (C++)...")
    classical_cp = run_classical_eval(fens_all)
    classical_scores = np.tanh(classical_cp / CP_SCALE)

    print("Running neural eval...")
    neural_scores = run_neural_eval(fens_all)

    # Directional accuracy (vs material) — same metric as the neural visualizer
    correct = (
        ((classical_scores > 0.05) & (materials > 0.5)) |
        ((classical_scores < -0.05) & (materials < -0.5)) |
        ((np.abs(classical_scores) <= 0.10) & (np.abs(materials) <= 1.0))
    )
    n_correct = int(correct.sum())
    print(f"Classical: {n_correct:,}/{n:,} correct ({100*n_correct/n:.2f}%)")

    # Best-fit alpha for ideal tanh curve
    from scipy.optimize import minimize_scalar
    alpha = minimize_scalar(
        lambda a: np.mean((classical_scores - np.tanh(a * materials)) ** 2),
        bounds=(0.01, 5.0), method="bounded",
    ).x
    print(f"Classical best-fit alpha: {alpha:.4f}")

    # Agreement with neural eval (sign agreement on non-equal positions)
    sig_mask = np.abs(neural_scores) > 0.1
    agree = np.sign(classical_scores[sig_mask]) == np.sign(neural_scores[sig_mask])
    print(f"Classical vs Neural sign agreement: {100*agree.mean():.2f}% on {sig_mask.sum():,} non-equal positions")

    # ---------- Plot ----------
    fig = plt.figure(figsize=(20, 12), facecolor="#0f0f23")
    fig.suptitle(f"Classical Evaluator Performance — {n:,} positions",
                 fontsize=18, fontweight="bold", color="white")
    gs = fig.add_gridspec(2, 3, hspace=0.32, wspace=0.28)

    def style(ax):
        ax.set_facecolor("#1a1a2e")
        ax.tick_params(colors="white")
        for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
        for sp in ["bottom", "left"]: ax.spines[sp].set_color("#444")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")

    # 1. Material vs classical eval (subsample)
    ax = fig.add_subplot(gs[0, 0])
    sample = np.random.choice(n, size=min(5000, n), replace=False)
    dot_colors = np.where(correct[sample], "#2ecc71", "#e74c3c")
    ax.scatter(materials[sample], classical_scores[sample],
               c=dot_colors, s=6, alpha=0.5, edgecolors="none")
    x = np.linspace(materials.min() - 1, materials.max() + 1, 300)
    ax.plot(x, np.tanh(alpha * x), color="#e74c3c", linewidth=1.5,
            linestyle="--", label=f"Best fit tanh({alpha:.2f}·m)")
    ax.axhline(0, color="#555", linewidth=0.5)
    ax.axvline(0, color="#555", linewidth=0.5)
    ax.set_xlabel("Material Advantage (pawns)")
    ax.set_ylabel("Classical Score (tanh-scaled)")
    ax.set_title("Material vs Classical Eval")
    ax.legend(fontsize=8, facecolor="#1a1a2e", labelcolor="white")
    style(ax)

    # 2. Score distribution
    ax = fig.add_subplot(gs[0, 1])
    ax.hist(classical_scores, bins=100, color="#9b59b6", edgecolor="#1a1a2e", alpha=0.85)
    ax.axvline(0, color="white", linewidth=0.6)
    ax.set_xlabel("Classical Score")
    ax.set_ylabel("Count")
    ax.set_title("Score Distribution")
    style(ax)

    # 3. Pie - directional accuracy
    ax = fig.add_subplot(gs[0, 2])
    ax.set_facecolor("#1a1a2e")
    ax.pie([n_correct, n - n_correct],
           labels=[f"Correct ({n_correct:,})", f"Wrong ({n - n_correct:,})"],
           colors=["#2ecc71", "#e74c3c"],
           autopct="%1.1f%%", startangle=90,
           textprops={"color": "white", "fontsize": 11})
    ax.set_title("Directional Accuracy", color="white")

    # 4. Classical vs Neural scatter
    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(classical_scores[sample], neural_scores[sample],
               c="#3498db", s=5, alpha=0.4, edgecolors="none")
    ax.plot([-1, 1], [-1, 1], color="white", linestyle="--", linewidth=1, label="y = x")
    ax.set_xlabel("Classical Score")
    ax.set_ylabel("Neural Score")
    ax.set_title(f"Classical vs Neural ({100*agree.mean():.1f}% sign agree)")
    ax.legend(fontsize=8, facecolor="#1a1a2e", labelcolor="white")
    style(ax)

    # 5. Accuracy by material magnitude
    ax = fig.add_subplot(gs[1, 1])
    bins = [(-100, -5), (-5, -2), (-2, -0.5), (-0.5, 0.5), (0.5, 2), (2, 5), (5, 100)]
    bin_labels = ["≤-5", "-5..-2", "-2..-0.5", "≈0", "0.5..2", "2..5", "≥5"]
    accs, counts = [], []
    for lo, hi in bins:
        mask = (materials > lo) & (materials <= hi)
        if mask.sum() > 0:
            accs.append(100 * correct[mask].mean())
            counts.append(int(mask.sum()))
        else:
            accs.append(0); counts.append(0)
    x = np.arange(len(bins))
    ax.bar(x, accs, color="#1abc9c", edgecolor="white", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(bin_labels, fontsize=9)
    ax.set_ylim(0, 115)
    ax.set_xlabel("Material Advantage Range")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy by Material Magnitude")
    for i, (v, c) in enumerate(zip(accs, counts)):
        ax.text(i, v + 1, f"{v:.0f}%\n(n={c:,})", ha="center", color="white", fontsize=8)
    style(ax)

    # 6. Disagreement distribution: |classical - neural|
    ax = fig.add_subplot(gs[1, 2])
    diff = np.abs(classical_scores - neural_scores)
    ax.hist(diff, bins=80, color="#f39c12", edgecolor="#1a1a2e", alpha=0.85)
    ax.set_xlabel("|Classical − Neural|")
    ax.set_ylabel("Count")
    ax.set_title(f"Disagreement (mean={diff.mean():.3f}, median={np.median(diff):.3f})")
    style(ax)

    out = "evaluator/classical_eval/classical_performance.png"
    plt.savefig(out, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved to {out}")
    plt.show()


if __name__ == "__main__":
    main()
