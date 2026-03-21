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


def engine_move(fen: str) -> str:
    """
    Placeholder — will call C++ engine + PyTorch model later.
    Returns a UCI move string e.g. 'e2e4'
    """
    board = chess.Board(fen)
    # TODO: replace with actual C++ engine + ML call
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return str(legal_moves[0])  # placeholder: first legal move


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
    pgn_so_far = data.get("pgn_so_far", "") # e.g. "1. e4 e5 2. Nf3"
    necai_color = data.get("color", "white") # "white" or "black"

    board = chess.Board(fen)

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

    # Case 1: Starting position + NECAI is white
    if fen == STARTING_FEN and necai_color == "white":
        chosen_move_uci = "e2e4"
        source = "hardcoded"

    # Case 2: Check opening book
    if chosen_move_uci is None:
        book_move = get_book_move(pgn_so_far)
        if book_move:
            # Convert SAN to UCI
            try:
                move = board.parse_san(book_move)
                chosen_move_uci = move.uci()
                source = "opening_book"
            except Exception:
                chosen_move_uci = None

    # Case 3: Fallback to engine + machine learning
    if chosen_move_uci is None:
        chosen_move_uci = engine_move(fen)
        source = "engine"

    # Apply the move
    move = chess.Move.from_uci(chosen_move_uci)
    san  = board.san(move)
    board.push(move)

    updated_fen    = board.fen()
    opponent_check = board.is_check()

    return jsonify({
        "move": san,             
        "move_uci": chosen_move_uci, 
        "fen": updated_fen,      
        "in_check": opponent_check,  
        "source": source,
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

if __name__ == "__main__":
    app.run(debug=True, port=5001)