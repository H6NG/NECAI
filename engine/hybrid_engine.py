"""
Hybrid chess engine: classical negamax search → top-K candidates → neural rerank.

Pipeline:
  1. Run classical negamax at full depth, get top K moves (fast)
  2. Apply each move, evaluate resulting FEN with batched neural eval
  3. Blend: 0.4 * classical_norm + 0.6 * neural
  4. Pick the highest-blended move

Usage:
    make top_moves
    python -m engine.hybrid_engine "<fen>" <depth> [k]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOP_MOVES_BIN = ROOT / "top_moves"

CLASSICAL_BLEND = 0.4
NEURAL_BLEND = 0.6
DEFAULT_K = 5

# Classical eval is in centipawns from White's perspective; map to tanh space
# the same way training did.
CP_SCALE = 600.0


def get_classical_candidates(fen: str, depth: int, k: int):
    """Run the C++ binary and parse its top-K output."""
    if not TOP_MOVES_BIN.exists():
        raise FileNotFoundError(f"{TOP_MOVES_BIN} not found. Run `make top_moves`.")

    result = subprocess.run(
        [str(TOP_MOVES_BIN), fen, str(depth), str(k)],
        capture_output=True, text=True, check=True,
    )

    candidates = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split(" ", 2)
        uci, score_str, after_fen = parts[0], parts[1], parts[2]
        candidates.append({
            "move": uci,
            "classical_cp": int(score_str),
            "after_fen": after_fen,
        })
    return candidates


def neural_scores(fens):
    """Batch-evaluate FENs with the trained neural model."""
    from evaluator.neural_eval.fast_inference import predict_batch
    return predict_batch(fens)


def normalize_classical(cp_score: int, white_to_move: bool) -> float:
    """Centipawns → tanh score from the side-to-move's perspective.

    The C++ search returns scores from the side-to-move's perspective already
    (negamax convention). We just rescale into [-1, 1].
    """
    return float(np.tanh(cp_score / CP_SCALE))


def neural_from_white_perspective(score: float, white_to_move_after: bool) -> float:
    """Neural model returns score from White's perspective. Convert to
    side-to-move (after the candidate move) so we can compare to classical."""
    return score if white_to_move_after else -score


def pick_best(fen: str, depth: int, k: int = DEFAULT_K, verbose: bool = True):
    candidates = get_classical_candidates(fen, depth, k)
    if not candidates:
        return None

    # White-to-move flag flips after each candidate move.
    white_to_move = fen.split()[1] == "w"

    after_fens = [c["after_fen"] for c in candidates]
    nn_scores = neural_scores(after_fens)

    for c, nn_raw in zip(candidates, nn_scores):
        # Classical score from search is already in side-to-move-of-original
        # perspective. We want both metrics in the same frame; compare from
        # the side that just moved (i.e. the original mover).
        classical_norm = normalize_classical(c["classical_cp"], white_to_move)

        # Neural score is from White's perspective. Flip if the original
        # mover was Black so high = good for the mover.
        neural_for_mover = nn_raw if white_to_move else -nn_raw

        c["classical_norm"] = classical_norm
        c["neural"] = float(neural_for_mover)
        c["blended"] = CLASSICAL_BLEND * classical_norm + NEURAL_BLEND * neural_for_mover

    candidates.sort(key=lambda c: c["blended"], reverse=True)

    if verbose:
        print(f"\n{'move':6}  {'cp':>6}  {'cls_norm':>9}  {'neural':>7}  {'blended':>8}")
        for c in candidates:
            print(f"{c['move']:6}  {c['classical_cp']:>6}  "
                  f"{c['classical_norm']:>9.3f}  {c['neural']:>7.3f}  "
                  f"{c['blended']:>8.3f}")

    return candidates[0]


def main():
    if len(sys.argv) < 3:
        print(f"Usage: python -m engine.hybrid_engine \"<fen>\" <depth> [k]")
        sys.exit(1)

    fen = sys.argv[1]
    depth = int(sys.argv[2])
    k = int(sys.argv[3]) if len(sys.argv) >= 4 else DEFAULT_K

    best = pick_best(fen, depth, k, verbose=True)
    if best is None:
        print(json.dumps({"best_move": None, "game_over": True}))
        return

    print("\n" + json.dumps({
        "best_move": best["move"],
        "classical_cp": best["classical_cp"],
        "neural_score": round(best["neural"], 4),
        "blended_score": round(best["blended"], 4),
    }))


if __name__ == "__main__":
    main()
