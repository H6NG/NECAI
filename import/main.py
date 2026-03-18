import zstandard as zstd
import chess.pgn
import requests
import io
import pandas as pd
from datasets import Dataset

URL = "https://database.lichess.org/standard/lichess_db_standard_rated_2026-02.pgn.zst"

def stream_lichess(url, max_games=10000):
    positions = []
    game_count = 0
    filtered_count = 0

    with requests.get(url, stream=True) as r:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(r.raw) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8")
            
            while game_count < max_games:
                game = chess.pgn.read_game(text_stream)
                if game is None:
                    break

                white_elo = int(game.headers.get("WhiteElo", 0))
                black_elo = int(game.headers.get("BlackElo", 0))
                result = game.headers.get("Result", "*")

                if white_elo >= 2000 and black_elo >= 2000 and result != "*":
                    board = game.board()
                    for move in game.mainline_moves():
                        board.push(move)
                        positions.append({
                            "fen": board.fen(),
                            "result": result,
                            "white_elo": white_elo,
                            "black_elo": black_elo
                        })
                    filtered_count += 1

                game_count += 1
                if game_count % 100 == 0:
                    print(f"Scanned: {game_count} | Kept: {filtered_count} | Positions: {len(positions)}")

    return positions

# Run
positions = stream_lichess(URL)

# Push to Hugging Face
df = pd.DataFrame(positions)
dataset = Dataset.from_pandas(df)
dataset.push_to_hub("h4ng/necai")

print(f"Done! {len(df)} positions uploaded to Hugging Face")