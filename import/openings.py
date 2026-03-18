import requests
import pandas as pd
import chess
import chess.pgn
import io
from datasets import Dataset

def pgn_to_fen(pgn_string):
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        return board.fen()
    except:
        return ""

def fetch_eco_openings():
    urls = [
        "https://raw.githubusercontent.com/lichess-org/chess-openings/master/a.tsv",
        "https://raw.githubusercontent.com/lichess-org/chess-openings/master/b.tsv",
        "https://raw.githubusercontent.com/lichess-org/chess-openings/master/c.tsv",
        "https://raw.githubusercontent.com/lichess-org/chess-openings/master/d.tsv",
        "https://raw.githubusercontent.com/lichess-org/chess-openings/master/e.tsv"
    ]

    all_openings = []

    for url in urls:
        response = requests.get(url)
        lines = response.text.strip().split("\n")

        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) >= 3:
                pgn = parts[2]
                fen = pgn_to_fen(pgn)
                all_openings.append({
                    "eco": parts[0],
                    "name": parts[1],
                    "pgn": pgn,
                    "fen": fen
                })

    return all_openings

print("Fetching ECO openings...")
openings = fetch_eco_openings()
print(f"Found {len(openings)} openings")

df = pd.DataFrame(openings)
dataset = Dataset.from_pandas(df)

dataset.push_to_hub(
    "h4ng/necai",
    config_name="openings",
    split="train"
)

print(f"Done! {len(df)} openings uploaded to h4ng/necai")