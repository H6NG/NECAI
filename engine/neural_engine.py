"""Neural engine: depth-2 minimax with batched neural leaf evaluation.

All positions at the leaf level are collected first, then evaluated in a
single batched forward pass — far faster than calling the model node-by-node.
"""
import chess
from evaluator.neural_eval.fast_inference import predict_batch, load_model

_CHECKMATE = 1.0
_STALEMATE = 0.0


def _order_moves(board: chess.Board):
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: board.is_capture(m), reverse=True)
    return moves


def neural_search(fen: str, depth: int = 2) -> dict:
    """Pick the best move using batched neural leaf evaluation.

    Returns the same shape as the C++ engine:
      {"best_move": uci_str, "engine_eval": int_centipawns, "game_over": bool}
    engine_eval is neural_score * 1000 (pseudo-centipawns for the eval bar).
    """
    load_model()
    board = chess.Board(fen)
    white_to_move = board.turn == chess.WHITE

    root_moves = _order_moves(board)
    if not root_moves:
        reason = "checkmate" if board.is_check() else "stalemate"
        return {"best_move": None, "engine_eval": None, "game_over": True, "reason": reason}

    if depth <= 1:
        result = _depth1(board, root_moves, white_to_move)
    else:
        result = _depth2(board, root_moves, white_to_move)

    neural_score = result.pop("neural_score", 0.0)
    result["engine_eval"] = int(neural_score * 1000)
    return result


# ── depth-1 ──────────────────────────────────────────────────────────────────

def _depth1(board, root_moves, white_to_move):
    leaf_fens, is_terminal, terminal_vals = [], [], []

    for move in root_moves:
        board.push(move)
        moves_after = list(board.legal_moves)
        if not moves_after:
            is_terminal.append(True)
            if board.is_check():
                terminal_vals.append(_CHECKMATE if white_to_move else -_CHECKMATE)
            else:
                terminal_vals.append(_STALEMATE)
            leaf_fens.append(None)
        else:
            is_terminal.append(False)
            terminal_vals.append(None)
            leaf_fens.append(board.fen())
        board.pop()

    non_terminal = [f for f in leaf_fens if f is not None]
    score_map = dict(zip(non_terminal, predict_batch(non_terminal))) if non_terminal else {}

    scored = []
    for move, terminal, tv, fen in zip(root_moves, is_terminal, terminal_vals, leaf_fens):
        score = tv if terminal else score_map[fen]
        scored.append((move, score))

    if white_to_move:
        best_move, best_score = max(scored, key=lambda x: x[1])
    else:
        best_move, best_score = min(scored, key=lambda x: x[1])

    return {"best_move": best_move.uci(), "neural_score": round(float(best_score), 4), "game_over": False}


# ── depth-2 ──────────────────────────────────────────────────────────────────

def _depth2(board, root_moves, white_to_move):
    # tree[uci1] = list of (fen_after_move2, terminal_score_or_None, is_terminal)
    tree = {}
    root_terminal = {}  # uci1 -> score when game ends after move1
    leaf_fens_set = set()

    for move1 in root_moves:
        uci1 = move1.uci()
        board.push(move1)

        opp_moves = _order_moves(board)
        if not opp_moves:
            if board.is_check():
                root_terminal[uci1] = _CHECKMATE if white_to_move else -_CHECKMATE
            else:
                root_terminal[uci1] = _STALEMATE
            board.pop()
            continue

        entries = []
        for move2 in opp_moves:
            board.push(move2)
            fen2 = board.fen()
            moves_after = list(board.legal_moves)
            if not moves_after:
                if board.is_check():
                    # Opponent delivered checkmate — bad for the original mover
                    score = -_CHECKMATE if white_to_move else _CHECKMATE
                else:
                    score = _STALEMATE
                entries.append((fen2, score, True))
            else:
                leaf_fens_set.add(fen2)
                entries.append((fen2, None, False))
            board.pop()

        tree[uci1] = entries
        board.pop()

    leaf_fens = list(leaf_fens_set)
    score_map = dict(zip(leaf_fens, predict_batch(leaf_fens))) if leaf_fens else {}

    opp_is_white = not white_to_move
    best_uci = None
    best_score = -float("inf") if white_to_move else float("inf")

    for move1 in root_moves:
        uci1 = move1.uci()
        if uci1 in root_terminal:
            move1_score = root_terminal[uci1]
        elif uci1 not in tree:
            continue
        else:
            entries = tree[uci1]
            leaf_scores = [
                ts if terminal else score_map.get(fen, 0.0)
                for fen, ts, terminal in entries
            ]
            # Opponent picks the best response for themselves
            move1_score = max(leaf_scores) if opp_is_white else min(leaf_scores)

        if white_to_move:
            if move1_score > best_score:
                best_score = move1_score
                best_uci = uci1
        else:
            if move1_score < best_score:
                best_score = move1_score
                best_uci = uci1

    if best_uci is None:
        best_uci = root_moves[0].uci()
        best_score = 0.0

    return {"best_move": best_uci, "neural_score": round(float(best_score), 4), "game_over": False}
