from flask import Flask, request, jsonify
from datasets import load_dataset
import chess
import chess.pgn
import io
import pandas as pd
from huggingface_hub import hf_hub_download

app = Flask(__name__); 

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

def engine_move(fen: str, depth: int = 3):
    """
    Calls the C++ engine executable and returns parsed JSON.
    """
    try:
        result = subprocess.run(
            [str(ENGINE_PATH), fen, str(depth)],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout.strip())
        return data

    except subprocess.CalledProcessError as e:
        print("Engine subprocess failed:")
        print(e.stderr)
        return None
    except json.JSONDecodeError:
        print("Engine returned invalid JSON")
        return None

def uci_to_san(fen: str, uci_move: str) -> str:
    """Convert UCI move (e2e4) to SAN (e4) for readability."""
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci_move)
    return board.san(move)


# MAIN ENDPOINT
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
        engine_data = engine_move(fen, depth=3)

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
            "game_over": True,
            "reason": "checkmate" if board.is_checkmate() else "stalemate"
        })

    engine_data = engine_move(fen, depth=depth)

    if engine_data is None:
        return jsonify({"error": "Engine call failed"}), 500

    return jsonify(engine_data)

if __name__ == "__main__":
    app.run(debug=True, port=5001)