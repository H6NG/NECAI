import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import time

from flask import Flask, request, jsonify
from datasets import load_dataset
import chess
import chess.pgn
import io
import pandas as pd
from huggingface_hub import hf_hub_download
from model.inference import predict_fen
from flask_cors import CORS

app = Flask(__name__); 
CORS(app, resources={r"/*": {"origins": "*"}})

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

print("Loading opening book...")
parquet_path = hf_hub_download(
    repo_id="h4ng/necai",
    filename="openings/train-00000-of-00001.parquet",
    repo_type="dataset"
)
df = pd.read_parquet(parquet_path).dropna(subset=["percentage"])
print(f"Opening book loaded: {len(df)} openings")


def get_book_move(moves_so_far: str) -> str | None:
    matches = df[df["pgn"].str.startswith(moves_so_far.strip())]
    if matches.empty:
        return None

    best = matches.sort_values("percentage", ascending=False).iloc[0]
    # example: "2. Nf3 Nc6 3. Bb5"
    remainder = best["pgn"][len(moves_so_far):].strip() 

    # Skip tokens that are move numbers like "2." or "12."
    for token in remainder.split(" "):
        token = token.strip()
        if token and not token.endswith(".") and token != "...":
            return token
            # return first real move token

    return None

def get_pgn_from_fen(fen: str) -> str:
    """Reconstruct moves played so far from FEN is not possible —
       caller must pass pgn_so_far alongside FEN."""
    return ""

import subprocess
import json
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parent.parent / "engine" / "cpp" / "necai_engine"

def engine_move(fen: str, depth: int = 2):
    try:
        t0 = time.time()

        result = subprocess.run(
            [str(ENGINE_PATH), fen, str(depth)],
            capture_output=True,
            text=True,
            check=True
        )

        t1 = time.time()
        print(f"[engine_move] subprocess took {t1 - t0:.4f}s")

        parse_start = time.time()
        data = json.loads(result.stdout.strip())
        parse_end = time.time()
        print(f"[engine_move] json parse took {parse_end - parse_start:.4f}s")

        return data

    except subprocess.CalledProcessError as e:
        print("[engine_move] subprocess failed")
        print(e.stderr)
        return None
    except json.JSONDecodeError:
        print("[engine_move] invalid JSON")
        print(result.stdout)
        return None
    
def uci_to_san(fen: str, uci_move: str) -> str:
    """Convert UCI move (e2e4) to SAN (e4) for readability."""
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci_move)
    return board.san(move)


"""# MAIN ENDPOINT
@app.route("/move", methods=["POST"])
def get_move():
    data = request.get_json()

    fen = data.get("fen", STARTING_FEN)
    pgn_so_far = data.get("pgn_so_far", "")
    necai_color = data.get("color", "white")  # "white" or "black"

    board = chess.Board(fen)

    # Check if it's actually the bot's turn
    is_white_turn = board.turn
    bot_is_white = (necai_color == "white")

    if is_white_turn != bot_is_white:
        return jsonify({
            "move": None,
            "fen": fen,
            "game_over": False,
            "message": "Not bot's turn"
        })

    # Check if game is already over
    if not list(board.legal_moves):
        return jsonify({
            "move": None,
            "fen": fen,
            "in_check": board.is_check(),
            "game_over": True,
            "reason": "checkmate" if board.is_checkmate() else "stalemate"
        })

    chosen_move_uci = None
    source = None
    engine_data = None

    # Case 1: Starting position + NECAI is white
    if fen == STARTING_FEN and necai_color == "white":
        chosen_move_uci = "e2e4"
        source = "hardcoded"

    # Case 2: Opening book
    if chosen_move_uci is None:
        book_move = get_book_move(pgn_so_far)
        if book_move:
            try:
                move = board.parse_san(book_move)
                chosen_move_uci = move.uci()
                source = "opening_book"
            except Exception:
                chosen_move_uci = None

    # Case 3: Engine fallback
    if chosen_move_uci is None:
        engine_data = engine_move(fen, depth=1)

        if engine_data is None:
            return jsonify({"error": "Engine call failed"}), 500

        if engine_data.get("game_over"):
            return jsonify({
                "move": None,
                "fen": fen,
                "in_check": board.is_check(),
                "game_over": True,
                "reason": engine_data.get("reason", "unknown")
            })

        chosen_move_uci = engine_data["best_move"]
        if not chosen_move_uci:
            return jsonify({
                "move": None,
                "fen": fen,
                "game_over": True,
                "reason": engine_data.get("reason", "no_move_returned")
            })
        source = "engine"

    # Apply chosen move
    move = chess.Move.from_uci(chosen_move_uci)
    san = board.san(move)
    board.push(move)

    updated_fen = board.fen()
    opponent_check = board.is_check()

    return jsonify({
        "move": san,
        "move_uci": chosen_move_uci,
        "fen": updated_fen,
        "in_check": opponent_check,
        "source": source,
        "engine_eval": engine_data.get("engine_eval") if engine_data else None,
        "game_over": False
    })
"""

@app.route("/move", methods=["POST"])
def get_move():
    total_start = time.time()
    print("\n========== /move ==========")

    req_start = time.time()
    data = request.get_json()
    req_end = time.time()
    print(f"[move] request.get_json: {req_end - req_start:.4f}s")

    fen = data.get("fen", STARTING_FEN)
    pgn_so_far = data.get("pgn_so_far", "")
    necai_color = data.get("color", "white")

    print(f"[move] bot color: {necai_color}")
    print(f"[move] fen: {fen}")
    print(f"[move] pgn: {pgn_so_far}")

    board_start = time.time()
    board = chess.Board(fen)
    board_end = time.time()
    print(f"[move] chess.Board(fen): {board_end - board_start:.4f}s")

    turn_start = time.time()
    is_white_turn = board.turn
    bot_is_white = (necai_color == "white")
    turn_end = time.time()
    print(f"[move] turn check prep: {turn_end - turn_start:.4f}s")

    if is_white_turn != bot_is_white:
        print("[move] early exit: not bot's turn")
        print(f"[move] TOTAL: {time.time() - total_start:.4f}s")
        return jsonify({
            "move": None,
            "fen": fen,
            "game_over": False,
            "message": "Not bot's turn"
        })

    legal_start = time.time()
    legal_moves = list(board.legal_moves)
    legal_end = time.time()
    print(f"[move] legal move generation: {legal_end - legal_start:.4f}s")
    print(f"[move] legal move count: {len(legal_moves)}")

    if not legal_moves:
        print("[move] early exit: no legal moves")
        print(f"[move] TOTAL: {time.time() - total_start:.4f}s")
        return jsonify({
            "move": None,
            "fen": fen,
            "in_check": board.is_check(),
            "game_over": True,
            "reason": "checkmate" if board.is_checkmate() else "stalemate"
        })

    chosen_move_uci = None
    source = None
    engine_data = None
    model_eval = None

    hardcoded_start = time.time()
    if fen == STARTING_FEN and necai_color == "white":
        chosen_move_uci = "e2e4"
        source = "hardcoded"
    hardcoded_end = time.time()
    print(f"[move] hardcoded opening check: {hardcoded_end - hardcoded_start:.4f}s")

    book_start = time.time()
    if chosen_move_uci is None and pgn_so_far.strip():
        book_move = get_book_move(pgn_so_far)
        if book_move:
            try:
                move = board.parse_san(book_move)
                chosen_move_uci = move.uci()
                source = "opening_book"
            except Exception as e:
                print("[move] opening book parse failed:", e)
                chosen_move_uci = None
    book_end = time.time()
    print(f"[move] opening book step: {book_end - book_start:.4f}s")
    print(f"[move] chosen after book: {chosen_move_uci}, source={source}")

    engine_start = time.time()
    if chosen_move_uci is None:
        engine_data = engine_move(fen, depth=2)
    engine_end = time.time()
    print(f"[move] engine step total: {engine_end - engine_start:.4f}s")

    if chosen_move_uci is None:
        if engine_data is None:
            print("[move] engine_data is None")
            print(f"[move] TOTAL: {time.time() - total_start:.4f}s")
            return jsonify({"error": "Engine call failed"}), 500

        if engine_data.get("game_over"):
            print("[move] engine says game over")
            print(f"[move] TOTAL: {time.time() - total_start:.4f}s")
            return jsonify({
                "move": None,
                "fen": fen,
                "in_check": board.is_check(),
                "game_over": True,
                "reason": engine_data.get("reason", "unknown")
            })

        chosen_move_uci = engine_data.get("best_move")
        source = "engine"
        print(f"[move] engine best move: {chosen_move_uci}")

        if not chosen_move_uci:
            print("[move] engine returned no move")
            print(f"[move] TOTAL: {time.time() - total_start:.4f}s")
            return jsonify({
                "move": None,
                "fen": fen,
                "game_over": True,
                "reason": engine_data.get("reason", "no_move_returned")
            })

    model_start = time.time()
    try:
        model_eval = predict_fen(fen)
    except Exception as e:
        print("[move] model inference failed:", e)
    model_end = time.time()
    print(f"[move] model eval step: {model_end - model_start:.4f}s")

    apply_start = time.time()
    move = chess.Move.from_uci(chosen_move_uci)
    san = board.san(move)
    board.push(move)
    updated_fen = board.fen()
    opponent_check = board.is_check()
    apply_end = time.time()
    print(f"[move] apply move + SAN + updated fen: {apply_end - apply_start:.4f}s")

    total_end = time.time()
    print(f"[move] TOTAL: {total_end - total_start:.4f}s")
    print("========== end /move ==========\n")

    return jsonify({
        "move": san,
        "move_uci": chosen_move_uci,
        "fen": updated_fen,
        "in_check": opponent_check,
        "source": source,
        "engine_eval": engine_data.get("engine_eval") if engine_data else None,
        "model_eval": model_eval,
        "game_over": False
    })
# debug func
@app.route("/debug", methods=["POST"])
def debug_book():
    data = request.get_json()
    pgn_so_far = data.get("pgn_so_far", "")
    
    matches = df[df["pgn"].str.startswith(pgn_so_far.strip())]
    
    return jsonify({
        "pgn_so_far": pgn_so_far,
        "matches_found": len(matches),
        "sample_pgns": df["pgn"].head(5).tolist(),  # show what DB actually looks like
        "sample_matches": matches["pgn"].head(3).tolist() if not matches.empty else []
    })

@app.route("/get_legal_move", methods=["POST"])
def get_legal_move(fen : str): 
    #this func returns all possible moves given a fen
    pass

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    fen = data.get("fen", STARTING_FEN)
    depth = data.get("depth", 3)

    board = chess.Board(fen)

    if not list(board.legal_moves):
        return jsonify({
            "best_move": None,
            "engine_eval": None,
            "model_eval": None,
            "game_over": True,
            "reason": "checkmate" if board.is_checkmate() else "stalemate"
        })

    engine_data = engine_move(fen, depth=depth)

    if engine_data is None:
        return jsonify({"error": "Engine call failed"}), 500

    try:
        model_eval = predict_fen(fen)
    except Exception as e:
        return jsonify({
            "error": f"Model inference failed: {str(e)}"
        }), 500

    return jsonify({
        "best_move": engine_data.get("best_move"),
        "engine_eval": engine_data.get("engine_eval"),
        "model_eval": model_eval,
        "game_over": engine_data.get("game_over", False)
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)